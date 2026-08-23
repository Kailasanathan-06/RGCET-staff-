"""
Department model — the primary isolation boundary for all data in the system.
Every resource, student, subject, and staff member belongs to a department.
"""
from django.db import models
from django.utils import timezone


class Department(models.Model):
    """
    Top-level isolation unit. Every piece of data in the system
    is scoped to a department — enforced at ORM level, not just UI.
    """
    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_INACTIVE, 'Inactive'),
    ]

    code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Short identifier e.g. CSE, ECE, MECH"
    )
    name = models.CharField(
        max_length=150,
        help_text="Full department name e.g. Computer Science and Engineering"
    )
    description = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'departments'
        ordering = ['name']
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'

    def __str__(self):
        return f"{self.code} — {self.name}"

    @property
    def is_active(self):
        return self.status == self.STATUS_ACTIVE
