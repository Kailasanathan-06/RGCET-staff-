"""
Department-level authorization mixins.

These are the core security layer. Every view that touches department data
must use one of these mixins. They enforce isolation at the ORM level,
not just the template level.

Usage:
    class ResourceDetailView(DepartmentAccessMixin, DetailView):
        model = Resource
        # Automatically blocks cross-dept access → 403
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import redirect
from django.contrib import messages


class LoginAndActiveRequiredMixin(LoginRequiredMixin):
    """
    Extends LoginRequiredMixin to also check that:
    1. The user has a StaffProfile
    2. The profile is active (not deactivated by admin)
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # Check profile exists and is active
        if not hasattr(request.user, 'profile'):
            messages.error(request, "Your account does not have a staff profile. Please contact admin.")
            return redirect('accounts:login')

        if not request.user.profile.is_active:
            messages.error(request, "Your account has been deactivated. Please contact admin.")
            return redirect('accounts:login')

        return super().dispatch(request, *args, **kwargs)


class RoleRequiredMixin(LoginAndActiveRequiredMixin):
    """
    Restricts access to views based on role.

    Usage:
        class DepartmentCreateView(RoleRequiredMixin, CreateView):
            allowed_roles = ['SUPER_ADMIN']
    """
    allowed_roles = []  # Override in subclass

    def dispatch(self, request, *args, **kwargs):
        result = super().dispatch(request, *args, **kwargs)
        if hasattr(result, 'status_code') and result.status_code != 200:
            return result

        profile = request.user.profile
        if self.allowed_roles and profile.role not in self.allowed_roles:
            raise PermissionDenied
        return result


class SuperAdminRequiredMixin(RoleRequiredMixin):
    """Shortcut: Super Admin only."""
    allowed_roles = ['SUPER_ADMIN']


class HODOrAboveMixin(RoleRequiredMixin):
    """Shortcut: HOD or Super Admin."""
    allowed_roles = ['SUPER_ADMIN', 'HOD']


class DepartmentAccessMixin(LoginAndActiveRequiredMixin):
    """
    The primary isolation mixin.

    For Super Admin: allows everything.
    For HOD/Teacher: scopes all querysets to their department.
    Raises PermissionDenied (403) if they try to access another department's object.

    Mix this into any view that returns department-scoped data.
    """

    def get_user_department(self):
        """Returns the user's department, or None for Super Admin (unrestricted)."""
        profile = self.request.user.profile
        if profile.is_super_admin:
            return None
        return profile.department

    def get_queryset(self):
        """
        Always scope the queryset to the user's department.
        Super Admin gets unscoped queryset.
        """
        qs = super().get_queryset()
        dept = self.get_user_department()
        if dept is not None:
            qs = qs.filter(department=dept)
        return qs

    @staticmethod
    def _model_has_department(model):
        """True if the model class exposes a `department` FK/field."""
        return model is not None and hasattr(model, 'department')

    def get_object(self, queryset=None):
        """
        After fetching the object, verify department ownership.
        This is the LAST LINE OF DEFENSE against IDOR attacks.

        Because get_queryset() is already department-scoped, a cross-department
        object would normally raise Http404 (object "not found"). We convert that
        into PermissionDenied (403) when the object exists but belongs to a
        different department — this is the behaviour the spec explicitly requires.
        """
        try:
            return super().get_object(queryset)
        except Http404:
            dept = self.get_user_department()
            model = getattr(self, 'model', None)
            pk = self.kwargs.get(self.pk_url_kwarg)
            if (
                dept is not None
                and pk is not None
                and self._model_has_department(model)
                and model.objects.filter(pk=pk).exclude(department=dept).exists()
            ):
                raise PermissionDenied
            raise


class TeacherSubjectAccessMixin(DepartmentAccessMixin):
    """
    Extra layer for Teacher role: also checks that the resource's subject
    is one this teacher is assigned to.

    HOD and Super Admin bypass the subject check.
    """

    def _get_teacher_subject_ids(self):
        """Return set of subject PKs this teacher is currently assigned to."""
        profile = self.request.user.profile
        if not profile.is_teacher:
            return None  # HOD/Super Admin: no restriction
        from subjects.models import TeacherSubject
        return set(
            TeacherSubject.objects.filter(teacher=profile)
            .values_list('subject_id', flat=True)
        )

    def get_queryset(self):
        qs = super().get_queryset()
        subject_ids = self._get_teacher_subject_ids()
        if subject_ids is not None:
            qs = qs.filter(subject_id__in=subject_ids)
        return qs

    def get_object(self, queryset=None):
        """
        DepartmentAccessMixin already converts cross-department access to 403.
        This layer additionally converts subject-level mismatch to 403:
        a teacher assigned to the department but NOT to this subject gets 403,
        not a misleading 404.
        """
        profile = self.request.user.profile
        try:
            return super().get_object(queryset)
        except Http404:
            if profile.is_teacher:
                pk = self.kwargs.get(self.pk_url_kwarg)
                model = getattr(self, 'model', None)
                subject_ids = self._get_teacher_subject_ids() or set()
                if (
                    model is not None
                    and pk is not None
                    and getattr(model, '_meta', None) is not None
                    and hasattr(model, 'subject')
                ):
                    same_dept_obj = model.objects.filter(
                        pk=pk, department=profile.department
                    ).first()
                    if same_dept_obj is not None and same_dept_obj.subject_id not in subject_ids:
                        raise PermissionDenied
            raise
