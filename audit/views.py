from django.shortcuts import render
from django.views.generic import ListView
from accounts.mixins import HODOrAboveMixin, DepartmentAccessMixin
from .models import AuditLog


class AuditLogListView(HODOrAboveMixin, DepartmentAccessMixin, ListView):
    """
    Displays audit logs.
    HOD is limited to their own department's audit logs.
    Super Admin sees all logs.
    """
    model = AuditLog
    template_name = 'audit/audit_list.html'
    context_object_name = 'logs'
    paginate_by = 50

    def get_queryset(self):
        # DepartmentAccessMixin scopes to user's department
        qs = super().get_queryset().select_related('user', 'department')
        
        # HOD: filter logs that belong to department or logs made by users in their department
        profile = self.request.user.profile
        if not profile.is_super_admin:
            qs = qs.filter(department=profile.department)

        # Filters
        action = self.request.GET.get('action')
        if action:
            qs = qs.filter(action=action)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['actions'] = AuditLog.ACTION_CHOICES
        ctx['current_filters'] = self.request.GET
        return ctx
