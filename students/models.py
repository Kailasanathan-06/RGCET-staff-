"""
Students model — always department-scoped.
A CSE teacher can NEVER retrieve ECE student records.
"""
from django.db import models
from django.utils import timezone
from departments.models import Department


class Student(models.Model):
    """
    Student record. The department FK is the primary isolation key.
    Every query in the system filters by department before returning data.
    """
    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'
    STATUS_GRADUATED = 'graduated'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_INACTIVE, 'Inactive'),
        (STATUS_GRADUATED, 'Graduated'),
    ]

    YEAR_CHOICES = [
        (1, '1st Year'),
        (2, '2nd Year'),
        (3, '3rd Year'),
        (4, '4th Year'),
    ]

    SEMESTER_CHOICES = [(i, f'Semester {i}') for i in range(1, 9)]

    # ── Identity ──────────────────────────────────────────────────────────────
    register_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="College register number — must be unique across all students"
    )
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)

    # ── Academic placement ────────────────────────────────────────────────────
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='students',
        db_index=True
    )
    batch = models.CharField(
        max_length=20,
        help_text="e.g. 2023-2027"
    )
    academic_year = models.CharField(
        max_length=20,
        help_text="Current academic year e.g. 2026-27"
    )
    year = models.PositiveSmallIntegerField(
        choices=YEAR_CHOICES,
        help_text="Current year of study"
    )
    semester = models.PositiveSmallIntegerField(
        choices=SEMESTER_CHOICES,
        null=True,
        blank=True
    )
    section = models.CharField(
        max_length=5,
        blank=True,
        null=True,
        help_text="Section A, B, C etc."
    )

    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'students'
        ordering = ['department', 'batch', 'section', 'name']
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        indexes = [
            models.Index(fields=['department', 'batch', 'year']),
            models.Index(fields=['department', 'section']),
        ]

    def __str__(self):
        return f"{self.register_number} — {self.name} ({self.department})"
