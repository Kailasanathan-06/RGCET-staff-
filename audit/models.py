"""
AuditLog model — immutable record of every significant action.
Never deleted. Used by HODs (own dept) and Super Admin (all).
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from departments.models import Department


class AuditLog(models.Model):
    """
    Immutable audit trail. Every write, download, import, and auth
    event is recorded here. Records are append-only — never updated.
    """
    # ── Action types ──────────────────────────────────────────────────────────
    ACTION_LOGIN = 'LOGIN'
    ACTION_LOGOUT = 'LOGOUT'
    ACTION_LOGIN_FAILED = 'LOGIN_FAILED'
    ACTION_UPLOAD = 'UPLOAD'
    ACTION_DOWNLOAD = 'DOWNLOAD'
    ACTION_UPDATE = 'UPDATE'
    ACTION_DELETE = 'DELETE'
    ACTION_EXCEL_IMPORT = 'EXCEL_IMPORT'
    ACTION_EXCEL_EXPORT = 'EXCEL_EXPORT'
    ACTION_USER_CREATE = 'USER_CREATE'
    ACTION_USER_DEACTIVATE = 'USER_DEACTIVATE'
    ACTION_SUBJECT_ASSIGN = 'SUBJECT_ASSIGN'
    ACTION_PERMISSION_CHANGE = 'PERMISSION_CHANGE'
    ACTION_PASSWORD_CHANGE = 'PASSWORD_CHANGE'
    ACTION_VIEW = 'VIEW'

    ACTION_CHOICES = [
        (ACTION_LOGIN, 'Login'),
        (ACTION_LOGOUT, 'Logout'),
        (ACTION_LOGIN_FAILED, 'Login Failed'),
        (ACTION_UPLOAD, 'File Upload'),
        (ACTION_DOWNLOAD, 'File Download'),
        (ACTION_UPDATE, 'Record Updated'),
        (ACTION_DELETE, 'Record Deleted'),
        (ACTION_EXCEL_IMPORT, 'Excel Import'),
        (ACTION_EXCEL_EXPORT, 'Excel Export'),
        (ACTION_USER_CREATE, 'User Created'),
        (ACTION_USER_DEACTIVATE, 'User Deactivated'),
        (ACTION_SUBJECT_ASSIGN, 'Subject Assigned'),
        (ACTION_PERMISSION_CHANGE, 'Permission Changed'),
        (ACTION_PASSWORD_CHANGE, 'Password Changed'),
        (ACTION_VIEW, 'Record Viewed'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    object_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Model name e.g. Resource, Student"
    )
    object_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="PK of the affected object"
    )
    description = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['department', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]

    def __str__(self):
        user_str = self.user.username if self.user else 'Anonymous'
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {user_str} — {self.action}"

    @classmethod
    def log(cls, user, action, description='', obj=None, department=None,
            ip_address=None, user_agent=None):
        """
        Convenience class method to create a log entry from anywhere.

        Usage:
            AuditLog.log(request.user, AuditLog.ACTION_UPLOAD,
                         description='Uploaded Data Structures notes',
                         obj=resource, department=resource.department,
                         ip_address=get_client_ip(request))
        """
        dept = department
        if dept is None and obj is not None and hasattr(obj, 'department'):
            dept = obj.department

        object_type = None
        object_id = None
        if obj is not None:
            object_type = obj.__class__.__name__
            object_id = str(obj.pk)

        cls.objects.create(
            user=user,
            department=dept,
            action=action,
            object_type=object_type,
            object_id=object_id,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
        )
