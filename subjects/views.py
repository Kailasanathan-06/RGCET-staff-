"""
Subjects views — create/update/deactivate subjects.
Super Admin manages all departments; HOD manages only their own department;
Teachers see only their assigned subjects (read-only list).
Also hosts the "Add Course" flow: create a subject + upload its materials.
"""
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
from django.db.models import Q
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from accounts.mixins import (
    LoginAndActiveRequiredMixin,
    RoleRequiredMixin,
    DepartmentAccessMixin,
)
from audit.models import AuditLog
from .models import Subject
from .forms import SubjectForm, CourseForm

MANAGE_ROLES = ['SUPER_ADMIN', 'HOD']


class SubjectListView(DepartmentAccessMixin, LoginAndActiveRequiredMixin, ListView):
    """Department-scoped subject list. Teachers see only their assigned subjects."""
    model = Subject
    template_name = 'subjects/list.html'
    context_object_name = 'subjects'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().filter(status='active').select_related(
            'department', 'academic_year', 'regulation'
        )

        profile = self.request.user.profile
        if profile.is_teacher:
            from .models import TeacherSubject
            assigned_ids = TeacherSubject.objects.filter(
                teacher=profile
            ).values_list('subject_id', flat=True)
            qs = qs.filter(id__in=assigned_ids)

        # Filter by department dropdown (super admin only)
        dept_filter = self.request.GET.get('department')
        if dept_filter and profile.is_super_admin:
            qs = qs.filter(department_id=dept_filter)

        # Search
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(Q(code__icontains=q) | Q(name__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from departments.models import Department
        profile = self.request.user.profile
        if profile.is_super_admin:
            ctx['departments'] = Department.objects.filter(status='active')
        else:
            ctx['departments'] = Department.objects.filter(pk=profile.department_id)
        ctx['current_filters'] = self.request.GET
        return ctx


class SubjectCreateView(RoleRequiredMixin, DepartmentAccessMixin, CreateView):
    allowed_roles = MANAGE_ROLES
    model = Subject
    form_class = SubjectForm
    template_name = 'subjects/form.html'
    success_url = reverse_lazy('subjects:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['staff_profile'] = self.request.user.profile
        return kwargs

    def form_valid(self, form):
        self.object = form.save()
        AuditLog.log(
            user=self.request.user,
            action=AuditLog.ACTION_UPLOAD,
            description=f"Created subject: {self.object.code} — {self.object.name}",
            obj=self.object,
            ip_address=self.request.client_ip,
            user_agent=self.request.user_agent,
        )
        messages.success(self.request, f"✓ Subject '{self.object.code}' created successfully.")
        return redirect(self.success_url)


class SubjectUpdateView(RoleRequiredMixin, DepartmentAccessMixin, UpdateView):
    allowed_roles = MANAGE_ROLES
    model = Subject
    form_class = SubjectForm
    template_name = 'subjects/form.html'
    success_url = reverse_lazy('subjects:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['staff_profile'] = self.request.user.profile
        return kwargs

    def form_valid(self, form):
        self.object = form.save()
        AuditLog.log(
            user=self.request.user,
            action=AuditLog.ACTION_UPDATE,
            description=f"Updated subject: {self.object.code} — {self.object.name}",
            obj=self.object,
            ip_address=self.request.client_ip,
            user_agent=self.request.user_agent,
        )
        messages.success(self.request, f"✓ Subject '{self.object.code}' updated successfully.")
        return redirect(self.success_url)


class SubjectDeleteView(RoleRequiredMixin, DepartmentAccessMixin, DeleteView):
    """Subjects are deactivated, never hard-deleted (PROTECT constraints)."""
    allowed_roles = MANAGE_ROLES
    model = Subject
    template_name = 'subjects/confirm_delete.html'
    success_url = reverse_lazy('subjects:list')

    def form_valid(self, form):
        subject = self.get_object()
        subject.status = Subject.STATUS_INACTIVE
        subject.save(update_fields=['status', 'updated_at'])
        AuditLog.log(
            user=self.request.user,
            action=AuditLog.ACTION_USER_DEACTIVATE,
            description=f"Deactivated subject: {subject.code} — {subject.name}",
            obj=subject,
            ip_address=self.request.client_ip,
            user_agent=self.request.user_agent,
        )
        messages.success(self.request, f"Subject '{subject.code}' deactivated successfully.")
        return redirect(self.success_url)


class CourseCreateView(LoginAndActiveRequiredMixin, CreateView):
    """
    Add Course — any staff member can add a new course: it creates the
    subject record AND uploads its syllabus, question papers and notes in
    one step. Teachers/HODs are restricted to their own department.
    """
    model = Subject
    form_class = CourseForm
    template_name = 'subjects/course_add.html'
    success_url = reverse_lazy('subjects:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['staff_profile'] = self.request.user.profile
        return kwargs

    def form_valid(self, form):
        subject = form.save()
        profile = self.request.user.profile

        # Auto-assign the creating teacher so they can manage the course
        if profile.is_teacher:
            from .models import TeacherSubject
            TeacherSubject.objects.get_or_create(
                teacher=profile,
                subject=subject,
                academic_year=subject.academic_year,
                defaults={'assigned_by': profile},
            )

        resources = self._save_course_files(form, subject, profile)

        AuditLog.log(
            user=self.request.user,
            action=AuditLog.ACTION_UPLOAD,
            description=(
                f"Added course: {subject.code} — {subject.name} "
                f"({len(resources)} file(s) uploaded)"
            ),
            obj=subject,
            ip_address=self.request.client_ip,
            user_agent=self.request.user_agent,
        )

        message = f"✓ Course '{subject.code} — {subject.name}' added successfully."
        if resources:
            message += f" {len(resources)} file(s) uploaded."
        messages.success(self.request, message)
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below and try again.")
        return super().form_invalid(form)

    def _save_course_files(self, form, subject, profile):
        """Attach uploaded syllabus / QP / notes files to the new subject."""
        from resources.models import Resource, ResourceCategory

        category_map = {
            'syllabus_files': ('syllabus', 'Syllabus'),
            'question_paper_files': ('question-papers', 'Question Papers'),
            'notes_files': ('notes', 'Notes'),
        }
        created = []
        for field_name, (slug, name) in category_map.items():
            files = form.cleaned_data.get(field_name) or []
            if not files:
                continue
            category, _ = ResourceCategory.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'description': name},
            )
            for uploaded_file in files:
                resource = Resource(
                    title=f"{subject.code} — {name}",
                    description=f"Uploaded with course {subject.code} — {subject.name}",
                    department=subject.department,
                    subject=subject,
                    category=category,
                    academic_year=subject.academic_year,
                    semester=subject.semester,
                    file=uploaded_file,
                    file_name=uploaded_file.name,
                    file_size=uploaded_file.size,
                    file_type=uploaded_file.content_type or '',
                    uploaded_by=profile,
                    status=Resource.STATUS_ACTIVE,
                )
                resource.save()
                created.append(resource)
        return created
