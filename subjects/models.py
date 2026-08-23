"""
Subjects models: AcademicYear, Regulation, Semester, Subject, TeacherSubject.
Subjects are scoped to departments and link teachers to resources.
"""
from django.db import models
from django.utils import timezone
from departments.models import Department


class AcademicYear(models.Model):
    """Dynamic academic year — Super Admin creates these. Never hard-coded."""
    name = models.CharField(
        max_length=20,
        unique=True,
        help_text="e.g. 2024-25, 2025-26"
    )
    start_year = models.PositiveIntegerField(help_text="e.g. 2024")
    end_year = models.PositiveIntegerField(help_text="e.g. 2025")
    is_current = models.BooleanField(
        default=False,
        help_text="Mark one year as the current active year"
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'academic_years'
        ordering = ['-start_year']
        verbose_name = 'Academic Year'
        verbose_name_plural = 'Academic Years'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Ensure only one year is marked as current."""
        if self.is_current:
            AcademicYear.objects.exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class Regulation(models.Model):
    """
    Regulation/Curriculum version — stored as a model so admins can
    add new regulations (R2017, R2019, R2021, R2025 etc.) without code changes.
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
        help_text="e.g. R2017, R2019, R2021"
    )
    name = models.CharField(
        max_length=100,
        help_text="Full name e.g. Regulation 2021"
    )
    description = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'regulations'
        ordering = ['-code']
        verbose_name = 'Regulation'
        verbose_name_plural = 'Regulations'

    def __str__(self):
        return self.code


class Subject(models.Model):
    """
    Academic subject. Always belongs to a department.
    The department FK is the primary isolation key for resource queries.
    """
    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_INACTIVE, 'Inactive'),
    ]

    SEMESTER_CHOICES = [(i, f'Semester {i}') for i in range(1, 9)]

    code = models.CharField(
        max_length=20,
        help_text="Subject code e.g. CS3301"
    )
    name = models.CharField(
        max_length=200,
        help_text="Full subject name e.g. Data Structures and Algorithms"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='subjects'
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name='subjects'
    )
    regulation = models.ForeignKey(
        Regulation,
        on_delete=models.PROTECT,
        related_name='subjects',
        null=True,
        blank=True
    )
    semester = models.PositiveSmallIntegerField(
        choices=SEMESTER_CHOICES,
        help_text="Semester number (1–8)"
    )
    credits = models.PositiveSmallIntegerField(default=3)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subjects'
        ordering = ['semester', 'name']
        unique_together = [('code', 'department', 'academic_year')]
        verbose_name = 'Subject'
        verbose_name_plural = 'Subjects'

    def __str__(self):
        return f"{self.code} — {self.name} (Sem {self.semester})"


class TeacherSubject(models.Model):
    """
    Junction table: which teacher is assigned to which subject.
    Stored with metadata (who assigned, when) — not a plain M2M.
    Teachers can ONLY upload resources for subjects in this table.
    """
    from accounts.models import StaffProfile

    teacher = models.ForeignKey(
        'accounts.StaffProfile',
        on_delete=models.CASCADE,
        related_name='subject_assignments'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='teacher_assignments'
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT
    )
    assigned_by = models.ForeignKey(
        'accounts.StaffProfile',
        on_delete=models.SET_NULL,
        null=True,
        related_name='assignments_made'
    )
    assigned_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'teacher_subjects'
        unique_together = [('teacher', 'subject', 'academic_year')]
        verbose_name = 'Teacher-Subject Assignment'
        verbose_name_plural = 'Teacher-Subject Assignments'

    def __str__(self):
        return f"{self.teacher} → {self.subject}"
