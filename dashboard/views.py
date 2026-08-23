from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from accounts.mixins import (
    LoginAndActiveRequiredMixin,
    HODOrAboveMixin,
    DepartmentAccessMixin,
)
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied


class DashboardHomeView(LoginAndActiveRequiredMixin, TemplateView):
    """Routes to role-specific dashboard template."""

    def get_template_names(self):
        profile = self.request.user.profile
        if profile.is_super_admin:
            return ['dashboard/superadmin_dashboard.html']
        elif profile.is_hod:
            return ['dashboard/hod_dashboard.html']
        else:
            return ['dashboard/teacher_dashboard.html']

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        profile = self.request.user.profile
        dept = profile.department

        if profile.is_super_admin:
            from departments.models import Department
            from accounts.models import StaffProfile
            from students.models import Student
            from resources.models import Resource
            ctx['total_departments'] = Department.objects.filter(status='active').count()
            ctx['total_staff'] = StaffProfile.objects.filter(status='active').count()
            ctx['total_students'] = Student.objects.filter(status='active').count()
            ctx['total_resources'] = Resource.objects.filter(status='active').count()
            ctx['recent_resources'] = Resource.objects.filter(
                status='active'
            ).select_related('subject', 'category', 'uploaded_by__user').order_by('-created_at')[:8]

        elif profile.is_hod and dept:
            from accounts.models import StaffProfile
            from students.models import Student
            from resources.models import Resource
            from subjects.models import Subject, TeacherSubject
            ctx['total_teachers'] = StaffProfile.objects.filter(
                department=dept, status='active', role='TEACHER'
            ).count()
            ctx['total_subjects'] = Subject.objects.filter(
                department=dept, status='active'
            ).count()
            ctx['total_students'] = Student.objects.filter(
                department=dept, status='active'
            ).count()
            ctx['total_resources'] = Resource.objects.filter(
                department=dept, status='active'
            ).count()
            ctx['recent_resources'] = Resource.objects.filter(
                department=dept, status='active'
            ).select_related('subject', 'category').order_by('-created_at')[:6]

            # ── Full department visibility for the HOD ──────────────────────
            ctx['dept_teachers'] = StaffProfile.objects.filter(
                department=dept, status='active'
            ).select_related('user').annotate(
                subject_count=Count('subject_assignments')
            ).order_by('role', 'user__first_name')
            ctx['dept_subjects'] = Subject.objects.filter(
                department=dept, status='active'
            ).annotate(
                teacher_count=Count('teacher_assignments')
            ).order_by('semester', 'code')
            ctx['student_year_summary'] = (
                Student.objects.filter(department=dept, status='active')
                .values('year')
                .annotate(count=Count('id'))
                .order_by('year')
            )
            ctx['recent_students'] = Student.objects.filter(
                department=dept
            ).order_by('-created_at')[:6]

        else:  # Teacher
            from subjects.models import TeacherSubject
            from resources.models import Resource, ResourceCategory
            assignments = TeacherSubject.objects.filter(
                teacher=profile
            ).select_related('subject__department', 'subject__regulation')
            subject_ids = [a.subject_id for a in assignments]
            ctx['assignments'] = assignments
            ctx['total_resources'] = Resource.objects.filter(
                uploaded_by=profile, status='active'
            ).count()

            # Resources available per assigned subject
            subject_resources = (
                Resource.objects.filter(
                    subject_id__in=subject_ids, status='active'
                ).values('subject_id').annotate(count=Count('id'))
            )
            ctx['subject_resource_counts'] = {
                item['subject_id']: item['count'] for item in subject_resources
            }

            # Per-category counts
            cats = ResourceCategory.objects.filter(is_active=True)
            ctx['category_counts'] = {
                cat.name: Resource.objects.filter(
                    uploaded_by=profile, category=cat, status='active'
                ).count()
                for cat in cats
            }
            ctx['recent_resources'] = Resource.objects.filter(
                uploaded_by=profile, status='active'
            ).select_related('subject', 'category').order_by('-created_at')[:5]

        return ctx


class ReportsView(HODOrAboveMixin, DepartmentAccessMixin, TemplateView):
    """
    Reports page.
    Super Admin sees college-wide reports; HOD sees only their department.
    """

    def get_template_names(self):
        return ['dashboard/reports.html']

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        profile = self.request.user.profile
        dept = profile.department

        from resources.models import Resource, ResourceCategory
        from subjects.models import Subject
        from students.models import Student
        from accounts.models import StaffProfile
        from audit.models import AuditLog

        if profile.is_super_admin:
            resource_qs = Resource.objects.filter(status='active')
            subject_qs = Subject.objects.filter(status='active')
            student_qs = Student.objects.filter(status='active')
            staff_qs = StaffProfile.objects.filter(status='active')
            audit_qs = AuditLog.objects.all()
        else:
            resource_qs = Resource.objects.filter(status='active', department=dept)
            subject_qs = Subject.objects.filter(status='active', department=dept)
            student_qs = Student.objects.filter(status='active', department=dept)
            staff_qs = StaffProfile.objects.filter(status='active', department=dept)
            audit_qs = AuditLog.objects.filter(department=dept)

        # ── Category-wise resource counts ──────────────────────────────────
        ctx['category_report'] = (
            resource_qs.values('category__name')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        # ── Subject-wise resource counts ───────────────────────────────────
        ctx['subject_report'] = (
            resource_qs.values('subject__code', 'subject__name')
            .annotate(count=Count('id'))
            .order_by('-count')[:15]
        )

        # ── Student counts by batch/section ────────────────────────────────
        ctx['student_batch_report'] = (
            student_qs.values('batch', 'year')
            .annotate(count=Count('id'))
            .order_by('batch', 'year')
        )
        ctx['student_section_report'] = (
            student_qs.values('section')
            .annotate(count=Count('id'))
            .order_by('section')
        )

        # ── Staff counts by role ───────────────────────────────────────────
        ctx['staff_role_report'] = (
            staff_qs.values('role')
            .annotate(count=Count('id'))
            .order_by('role')
        )

        # ── Upload activity (last 14 days) ─────────────────────────────────
        from datetime import timedelta
        from django.utils import timezone
        since = timezone.now() - timedelta(days=14)
        recent_logs = (
            audit_qs.filter(action=AuditLog.ACTION_UPLOAD, timestamp__gte=since)
            .values_list('timestamp', flat=True)
            .order_by('timestamp')
        )
        day_counts = {}
        for ts in recent_logs:
            day_key = ts.date()
            day_counts[day_key] = day_counts.get(day_key, 0) + 1
        ctx['upload_activity'] = sorted(
            [{'day': day, 'count': count} for day, count in day_counts.items()],
            key=lambda item: item['day'],
        )

        ctx['totals'] = {
            'resources': resource_qs.count(),
            'subjects': subject_qs.count(),
            'students': student_qs.count(),
            'teachers': staff_qs.filter(role=StaffProfile.ROLE_TEACHER).count(),
        }
        return ctx
