"""
Accounts models: StaffProfile extends Django's built-in User.
Role and department are attached here and checked on every request.
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from departments.models import Department


class StaffProfile(models.Model):
    """
    Extends Django's User model with college-specific attributes.
    role + department together form the primary authorization context.
    """
    ROLE_SUPER_ADMIN = 'SUPER_ADMIN'
    ROLE_HOD = 'HOD'
    ROLE_TEACHER = 'TEACHER'
    ROLE_CHOICES = [
        (ROLE_SUPER_ADMIN, 'Super Admin'),
        (ROLE_HOD, 'HOD / Department Admin'),
        (ROLE_TEACHER, 'Teacher / Staff'),
    ]

    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_INACTIVE, 'Inactive'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    employee_id = models.CharField(
        max_length=50,
        unique=True,
        help_text="College employee ID e.g. EMP001"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='staff',
        null=True,
        blank=True,
        help_text="Super Admin may have no department"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_TEACHER
    )
    phone = models.CharField(max_length=15, blank=True, null=True)
    profile_photo = models.ImageField(
        upload_to='staff/photos/',
        blank=True,
        null=True
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'staff_profiles'
        ordering = ['user__last_name', 'user__first_name']
        verbose_name = 'Staff Profile'
        verbose_name_plural = 'Staff Profiles'

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.role}) — {self.department}"

    # ── Convenience role checks ─────────────────────────────────────────────
    @property
    def is_super_admin(self):
        return self.role == self.ROLE_SUPER_ADMIN

    @property
    def is_hod(self):
        return self.role == self.ROLE_HOD

    @property
    def is_teacher(self):
        return self.role == self.ROLE_TEACHER

    @property
    def is_active(self):
        return self.status == self.STATUS_ACTIVE

    def can_access_department(self, department):
        """Core authorization check — used everywhere in the system."""
        if self.is_super_admin:
            return True
        return self.department == department

    def get_assigned_subjects(self):
        """Return queryset of subjects this teacher is currently assigned to."""
        from subjects.models import TeacherSubject
        return TeacherSubject.objects.filter(teacher=self).select_related('subject')
