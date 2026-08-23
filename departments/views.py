"""
Departments views — full CRUD, restricted to Super Admin only.
Department data is the top-level isolation boundary, so only the
Super Admin may create or modify departments. HOD/Teacher are blocked (403).
"""
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from accounts.mixins import SuperAdminRequiredMixin
from audit.models import AuditLog
from .models import Department
from .forms import DepartmentForm


class DepartmentListView(SuperAdminRequiredMixin, ListView):
    """Super Admin sees all departments with staff/subject/student counts."""
    model = Department
    template_name = 'departments/list.html'
    context_object_name = 'departments'
    paginate_by = 25

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        depts = self.object_list
        ctx['staff_counts'] = {
            d.id: d.staff.count() for d in depts
        }
        ctx['subject_counts'] = {
            d.id: d.subjects.count() for d in depts
        }
        ctx['student_counts'] = {
            d.id: d.students.count() for d in depts
        }
        return ctx


class DepartmentCreateView(SuperAdminRequiredMixin, CreateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'departments/form.html'
    success_url = reverse_lazy('departments:list')

    def form_valid(self, form):
        self.object = form.save()
        AuditLog.log(
            user=self.request.user,
            action=AuditLog.ACTION_UPLOAD,
            description=f"Created department: {self.object.code} — {self.object.name}",
            obj=self.object,
            ip_address=self.request.client_ip,
            user_agent=self.request.user_agent,
        )
        messages.success(self.request, f"✓ Department '{self.object.code}' created successfully.")
        return redirect(self.success_url)


class DepartmentUpdateView(SuperAdminRequiredMixin, UpdateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'departments/form.html'
    success_url = reverse_lazy('departments:list')

    def form_valid(self, form):
        self.object = form.save()
        AuditLog.log(
            user=self.request.user,
            action=AuditLog.ACTION_UPDATE,
            description=f"Updated department: {self.object.code}",
            obj=self.object,
            ip_address=self.request.client_ip,
            user_agent=self.request.user_agent,
        )
        messages.success(self.request, f"✓ Department '{self.object.code}' updated successfully.")
        return redirect(self.success_url)


class DepartmentDeleteView(SuperAdminRequiredMixin, DeleteView):
    """
    Departments are NOT hard-deleted — they are deactivated.
    PROTECT constraints on children prevent destructive cascades.
    """
    model = Department
    template_name = 'departments/confirm_delete.html'
    success_url = reverse_lazy('departments:list')

    def form_valid(self, form):
        dept = self.get_object()
        dept.status = Department.STATUS_INACTIVE
        dept.save(update_fields=['status', 'updated_at'])
        AuditLog.log(
            user=self.request.user,
            action=AuditLog.ACTION_USER_DEACTIVATE,
            description=f"Deactivated department: {dept.code}",
            obj=dept,
            ip_address=self.request.client_ip,
            user_agent=self.request.user_agent,
        )
        messages.success(self.request, f"Department '{dept.code}' deactivated successfully.")
        return redirect(self.success_url)
