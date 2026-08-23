"""
Resources views — Upload, List, Detail, Edit, Delete, and Secure Download.
Every view uses DepartmentAccessMixin or TeacherSubjectAccessMixin.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, Http404
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.db.models import Q

from audit.models import AuditLog
from accounts.mixins import (
    LoginAndActiveRequiredMixin,
    DepartmentAccessMixin,
    TeacherSubjectAccessMixin,
    HODOrAboveMixin,
)
from .models import Resource, ResourceCategory
from .forms import ResourceUploadForm, ResourceEditForm


class ResourceListView(DepartmentAccessMixin, ListView):
    """
    Lists resources. Always scoped to user's department (via DepartmentAccessMixin).
    Teachers further scoped to their assigned subjects.
    """
    model = Resource
    template_name = 'resources/resource_list.html'
    context_object_name = 'resources'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().filter(status='active').select_related(
            'subject', 'category', 'uploaded_by__user', 'department', 'academic_year'
        )
        profile = self.request.user.profile

        # Teacher: further scope to assigned subjects
        if profile.is_teacher:
            from subjects.models import TeacherSubject
            assigned_ids = TeacherSubject.objects.filter(
                teacher=profile
            ).values_list('subject_id', flat=True)
            qs = qs.filter(subject_id__in=assigned_ids)

        # Search
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(subject__name__icontains=q) |
                Q(subject__code__icontains=q)
            )

        # Filters
        category_id = self.request.GET.get('category')
        if category_id:
            qs = qs.filter(category_id=category_id)

        subject_id = self.request.GET.get('subject')
        if subject_id:
            qs = qs.filter(subject_id=subject_id)

        semester = self.request.GET.get('semester')
        if semester:
            qs = qs.filter(semester=semester)

        year_id = self.request.GET.get('academic_year')
        if year_id:
            qs = qs.filter(academic_year_id=year_id)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = ResourceCategory.objects.filter(is_active=True)
        ctx['current_filters'] = self.request.GET
        return ctx


class ResourceDetailView(TeacherSubjectAccessMixin, DetailView):
    """
    Detail page for a single resource.
    TeacherSubjectAccessMixin blocks cross-dept AND cross-subject access.
    """
    model = Resource
    template_name = 'resources/resource_detail.html'
    context_object_name = 'resource'


class ResourceUploadView(LoginAndActiveRequiredMixin, CreateView):
    """
    Upload a new resource. Subject choices filtered by role/assignments.
    """
    model = Resource
    form_class = ResourceUploadForm
    template_name = 'resources/resource_upload.html'
    success_url = reverse_lazy('resources:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['staff_profile'] = self.request.user.profile
        return kwargs

    def form_valid(self, form):
        resource = form.save(commit=False)
        profile = self.request.user.profile
        resource.uploaded_by = profile
        # Always set department from the subject (not user input)
        resource.department = resource.subject.department
        # Store original filename
        resource.file_name = form.cleaned_data['file'].name
        resource.file_size = form.cleaned_data['file'].size
        resource.file_type = form.cleaned_data['file'].content_type or ''
        resource.save()

        AuditLog.log(
            user=self.request.user,
            action=AuditLog.ACTION_UPLOAD,
            description=f"Uploaded: {resource.title}",
            obj=resource,
            ip_address=self.request.client_ip,
            user_agent=self.request.user_agent,
        )
        messages.success(self.request, f"✓ '{resource.title}' uploaded successfully.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below and try again.")
        return super().form_invalid(form)


class ResourceEditView(DepartmentAccessMixin, UpdateView):
    """Edit resource metadata. Only uploaded_by or HOD/Admin can edit."""
    model = Resource
    form_class = ResourceEditForm
    template_name = 'resources/resource_edit.html'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        profile = request.user.profile
        # Teacher can only edit their own uploads
        if profile.is_teacher and obj.uploaded_by != profile:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, "Resource updated successfully.")
        return reverse_lazy('resources:detail', kwargs={'pk': self.object.pk})


class ResourceDeleteView(DepartmentAccessMixin, DeleteView):
    """Delete a resource. Teacher only deletes own uploads."""
    model = Resource
    template_name = 'resources/resource_confirm_delete.html'
    success_url = reverse_lazy('resources:list')

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        profile = request.user.profile
        if profile.is_teacher and obj.uploaded_by != profile:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        resource = self.get_object()
        AuditLog.log(
            user=self.request.user,
            action=AuditLog.ACTION_DELETE,
            description=f"Deleted resource: {resource.title}",
            obj=resource,
            ip_address=self.request.client_ip,
        )
        messages.success(self.request, f"'{resource.title}' has been deleted.")
        return super().form_valid(form)


@login_required
def secure_download(request, pk):
    """
    Secure file download — NEVER serve files via /media/ URLs.

    Flow:
    1. Authenticate user
    2. Fetch resource object
    3. Check department access
    4. Check subject access (for teachers)
    5. Stream file
    6. Log download
    """
    resource = get_object_or_404(Resource, pk=pk, status='active')
    profile = request.user.profile

    if not profile.is_active:
        raise PermissionDenied

    # ── Department check ──────────────────────────────────────────────────────
    if not profile.is_super_admin:
        if resource.department != profile.department:
            AuditLog.log(
                user=request.user,
                action=AuditLog.ACTION_DOWNLOAD,
                description=f"BLOCKED: Unauthorized download attempt on resource {pk}",
                ip_address=request.client_ip,
            )
            raise PermissionDenied

    # ── Subject check for teachers ────────────────────────────────────────────
    if profile.is_teacher:
        from subjects.models import TeacherSubject
        is_assigned = TeacherSubject.objects.filter(
            teacher=profile,
            subject=resource.subject
        ).exists()
        if not is_assigned:
            AuditLog.log(
                user=request.user,
                action=AuditLog.ACTION_DOWNLOAD,
                description=f"BLOCKED: Teacher not assigned to subject for resource {pk}",
                ip_address=request.client_ip,
            )
            raise PermissionDenied

    # ── Serve file ────────────────────────────────────────────────────────────
    try:
        file_handle = resource.file.open('rb')
    except FileNotFoundError:
        raise Http404("The requested file no longer exists.")

    response = FileResponse(file_handle)
    response['Content-Type'] = resource.file_type or 'application/octet-stream'
    response['Content-Disposition'] = (
        f'attachment; filename="{resource.file_name}"'
    )
    response['Content-Length'] = resource.file_size

    AuditLog.log(
        user=request.user,
        action=AuditLog.ACTION_DOWNLOAD,
        description=f"Downloaded: {resource.title}",
        obj=resource,
        ip_address=request.client_ip,
        user_agent=request.user_agent,
    )
    return response
