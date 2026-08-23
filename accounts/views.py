"""
Accounts views: Login, Logout, Profile, Password Change, Staff Management, Error pages.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.views.generic import UpdateView, DetailView, ListView, CreateView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.db.models import Q
from audit.models import AuditLog
from .forms import (
    LoginForm,
    StaffCreateForm,
    RegisterForm,
    StaffProfileUpdateForm,
    CustomPasswordChangeForm,
    StaffResetPasswordForm,
)
from .models import StaffProfile
from .mixins import LoginAndActiveRequiredMixin, SuperAdminRequiredMixin
from departments.models import Department


# ── Authentication ─────────────────────────────────────────────────────────────

def login_view(request):
    """Login page — redirects to dashboard if already authenticated."""
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    form = LoginForm(request, data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()

            # Check profile active status
            if hasattr(user, 'profile') and not user.profile.is_active:
                messages.error(
                    request,
                    "Your account has been deactivated. Please contact the administrator."
                )
                AuditLog.log(
                    user=user,
                    action=AuditLog.ACTION_LOGIN_FAILED,
                    description='Login attempt on deactivated account',
                    ip_address=request.client_ip,
                    user_agent=request.user_agent,
                )
                return render(request, 'accounts/login.html', {'form': form})

            login(request, user)

            AuditLog.log(
                user=user,
                action=AuditLog.ACTION_LOGIN,
                department=getattr(getattr(user, 'profile', None), 'department', None),
                ip_address=request.client_ip,
                user_agent=request.user_agent,
            )

            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
            next_url = request.GET.get('next', 'dashboard:home')
            return redirect(next_url)
        else:
            # Log failed login attempt
            AuditLog.log(
                user=None,
                action=AuditLog.ACTION_LOGIN_FAILED,
                description=f"Failed login for username: {request.POST.get('username', '')}",
                ip_address=request.client_ip,
                user_agent=request.user_agent,
            )
            messages.error(request, "Invalid username or password. Please try again.")

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """Logout — logs the action then clears session."""
    AuditLog.log(
        user=request.user,
        action=AuditLog.ACTION_LOGOUT,
        department=getattr(getattr(request.user, 'profile', None), 'department', None),
        ip_address=request.client_ip,
        user_agent=request.user_agent,
    )
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('accounts:login')


# ── Profile ────────────────────────────────────────────────────────────────────

class ProfileView(LoginAndActiveRequiredMixin, DetailView):
    """Shows logged-in user's own profile."""
    model = StaffProfile
    template_name = 'accounts/profile.html'
    context_object_name = 'profile'

    def get_object(self):
        return self.request.user.profile


class ProfileUpdateView(LoginAndActiveRequiredMixin, UpdateView):
    """Staff updates their own profile (non-sensitive fields only)."""
    model = StaffProfile
    form_class = StaffProfileUpdateForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        return self.request.user.profile

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        return kwargs

    def form_valid(self, form):
        # Also update User's first/last name and email
        user = self.request.user
        user.first_name = form.cleaned_data.get('first_name', user.first_name)
        user.last_name = form.cleaned_data.get('last_name', user.last_name)
        user.email = form.cleaned_data.get('email', user.email)
        user.save()
        messages.success(self.request, "Your profile has been updated successfully.")
        return super().form_valid(form)


@login_required
def change_password_view(request):
    """Password change for logged-in staff."""
    form = CustomPasswordChangeForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        # Keep session alive after password change
        update_session_auth_hash(request, user)
        AuditLog.log(
            user=request.user,
            action=AuditLog.ACTION_PASSWORD_CHANGE,
            department=getattr(request.profile, 'department', None),
            ip_address=request.client_ip,
            user_agent=request.user_agent,
        )
        messages.success(request, "Your password has been changed successfully.")
        return redirect('accounts:profile')

    return render(request, 'accounts/change_password.html', {'form': form})


# ── Staff Management (Super Admin only) ────────────────────────────────────────

class StaffListView(SuperAdminRequiredMixin, ListView):
    """Super Admin views all staff accounts, with search and filters."""
    model = StaffProfile
    template_name = 'accounts/staff_list.html'
    context_object_name = 'staff_list'
    paginate_by = 25

    def get_queryset(self):
        qs = StaffProfile.objects.select_related('user', 'department').order_by(
            'user__last_name', 'user__first_name'
        )

        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(employee_id__icontains=q) |
                Q(user__first_name__icontains=q) |
                Q(user__last_name__icontains=q) |
                Q(user__username__icontains=q) |
                Q(user__email__icontains=q)
            )

        role = self.request.GET.get('role')
        if role:
            qs = qs.filter(role=role)

        dept = self.request.GET.get('department')
        if dept:
            qs = qs.filter(department_id=dept)

        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['departments'] = Department.objects.filter(status='active')
        ctx['current_filters'] = self.request.GET
        return ctx


class StaffDetailView(SuperAdminRequiredMixin, DetailView):
    """Super Admin views a staff member's full profile."""
    model = StaffProfile
    template_name = 'accounts/staff_detail.html'
    context_object_name = 'staff'


class StaffCreateView(SuperAdminRequiredMixin, CreateView):
    """Super Admin creates a new staff account (User + StaffProfile)."""
    model = StaffProfile
    form_class = StaffCreateForm
    template_name = 'accounts/staff_form.html'
    success_url = reverse_lazy('accounts:staff_list')

    def form_valid(self, form):
        user, profile = create_staff_account(
            form, assigned_by=self.request.user.profile,
        )

        AuditLog.log(
            user=self.request.user,
            action=AuditLog.ACTION_USER_CREATE,
            description=(
                f"Created staff account: {user.username} "
                f"({profile.get_role_display()}, {profile.department})"
            ),
            obj=profile,
            ip_address=self.request.client_ip,
            user_agent=self.request.user_agent,
        )
        messages.success(
            self.request,
            f"✓ User '{user.username}' created successfully. "
            f"Temporary password: {form.cleaned_data['password']}"
        )
        return redirect(self.success_url)


def create_staff_account(form, assigned_by=None):
    """Create the User + StaffProfile pair. Returns (user, profile)."""
    user = User.objects.create_user(
        username=form.cleaned_data['username'],
        password=form.cleaned_data['password'],
        first_name=form.cleaned_data['first_name'],
        last_name=form.cleaned_data['last_name'],
        email=form.cleaned_data['email'],
        is_staff=form.cleaned_data['role'] == StaffProfile.ROLE_SUPER_ADMIN,
        is_superuser=form.cleaned_data['role'] == StaffProfile.ROLE_SUPER_ADMIN,
    )
    profile = form.save(commit=False)
    profile.user = user
    profile.status = StaffProfile.STATUS_ACTIVE
    profile.save()
    return user, profile


def register_view(request):
    """Public sign-up from the login page — creates a Teacher or HOD account and logs the user in."""
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    form = RegisterForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user, profile = create_staff_account(form, assigned_by=None)

        AuditLog.log(
            user=None,
            action=AuditLog.ACTION_USER_CREATE,
            description=(
                f"Self-registered account: {user.username} "
                f"({profile.get_role_display()}, {profile.department})"
            ),
            obj=profile,
            ip_address=request.client_ip,
            user_agent=request.user_agent,
        )

        login(request, user)
        messages.success(
            request,
            f"✓ Account created. Welcome, {user.get_full_name() or user.username}!"
        )
        return redirect('dashboard:home')

    ctx = {
        'form': form,
        'register_mode': True,
    }
    return render(request, 'accounts/staff_form.html', ctx)


@login_required
def staff_toggle_active(request, pk):
    """Super Admin activates/deactivates a staff account."""
    if not hasattr(request.user, 'profile') or not request.user.profile.is_super_admin:
        raise PermissionDenied

    staff = get_object_or_404(StaffProfile, pk=pk)
    if staff.user == request.user:
        messages.error(request, "You cannot deactivate your own account.")
        return redirect('accounts:staff_detail', pk=pk)

    if staff.status == StaffProfile.STATUS_ACTIVE:
        staff.status = StaffProfile.STATUS_INACTIVE
        staff.user.is_active = False
        action = AuditLog.ACTION_USER_DEACTIVATE
        label = 'deactivated'
    else:
        staff.status = StaffProfile.STATUS_ACTIVE
        staff.user.is_active = True
        action = AuditLog.ACTION_USER_CREATE
        label = 'activated'

    staff.user.save(update_fields=['is_active'])
    staff.save(update_fields=['status', 'updated_at'])

    AuditLog.log(
        user=request.user,
        action=action,
        description=f"Staff account {label}: {staff.user.username}",
        obj=staff,
        ip_address=request.client_ip,
        user_agent=request.user_agent,
    )
    messages.success(request, f"Staff account '{staff.user.username}' {label} successfully.")
    return redirect('accounts:staff_detail', pk=pk)


@login_required
def staff_reset_password(request, pk):
    """Super Admin resets a staff member's password."""
    if not hasattr(request.user, 'profile') or not request.user.profile.is_super_admin:
        raise PermissionDenied

    staff = get_object_or_404(StaffProfile, pk=pk)
    form = StaffResetPasswordForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        new_password = form.cleaned_data['new_password']
        staff.user.set_password(new_password)
        staff.user.save()
        AuditLog.log(
            user=request.user,
            action=AuditLog.ACTION_PASSWORD_CHANGE,
            description=f"Admin reset password for: {staff.user.username}",
            obj=staff,
            ip_address=request.client_ip,
            user_agent=request.user_agent,
        )
        messages.success(request, f"Password for '{staff.user.username}' reset successfully.")
        return redirect('accounts:staff_detail', pk=pk)

    return render(request, 'accounts/staff_reset_password.html', {
        'form': form,
        'staff': staff,
    })


# ── Error Handlers ─────────────────────────────────────────────────────────────

def error_400(request, exception=None):
    return render(request, 'errors/400.html', status=400)

def error_403(request, exception=None):
    return render(request, 'errors/403.html', status=403)

def error_404(request, exception=None):
    return render(request, 'errors/404.html', status=404)

def error_500(request):
    return render(request, 'errors/500.html', status=500)
