"""
Resources models: ResourceCategory and Resource.
Resources are always department-scoped — the department FK on Resource
enables fast isolation without JOIN chains on every request.
"""
import os
import uuid
from django.db import models
from django.utils import timezone
from departments.models import Department
from subjects.models import Subject, AcademicYear


def resource_upload_path(instance, filename):
    """
    Store files at: media/resources/<dept_code>/<category_slug>/<uuid>.<ext>
    The path does NOT expose the original filename for security.
    """
    ext = os.path.splitext(filename)[1].lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    dept_code = instance.department.code if instance.department else 'general'
    category_slug = instance.category.slug if instance.category else 'misc'
    return f"resources/{dept_code}/{category_slug}/{unique_name}"


class ResourceCategory(models.Model):
    """
    Dynamic resource categories — admins can add new ones without code changes.
    e.g. Notes, Question Papers, Lab Manuals, Assignments, Study Materials, Syllabus
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Bootstrap icon class e.g. bi-file-earmark-text"
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'resource_categories'
        ordering = ['sort_order', 'name']
        verbose_name = 'Resource Category'
        verbose_name_plural = 'Resource Categories'

    def __str__(self):
        return self.name


class Resource(models.Model):
    """
    Core resource record. Every resource has:
    - department (denormalized for fast isolation check)
    - subject (for subject-level filtering)
    - category (Notes / QP / Lab Manual etc.)
    - a single uploaded file

    The file is NEVER served via /media/ URLs — always via SecureDownloadView.
    """
    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_INACTIVE, 'Inactive'),
    ]

    SEMESTER_CHOICES = [(i, f'Semester {i}') for i in range(1, 9)]
    UNIT_CHOICES = [(i, f'Unit {i}') for i in range(1, 6)]

    title = models.CharField(max_length=300, help_text="e.g. Data Structures Unit 1 Notes")
    description = models.TextField(blank=True, null=True)

    # ── Isolation keys (both indexed) ────────────────────────────────────────
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='resources',
        db_index=True
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name='resources',
        db_index=True
    )
    category = models.ForeignKey(
        ResourceCategory,
        on_delete=models.PROTECT,
        related_name='resources'
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name='resources'
    )
    semester = models.PositiveSmallIntegerField(
        choices=SEMESTER_CHOICES,
        null=True,
        blank=True
    )
    unit = models.PositiveSmallIntegerField(
        choices=UNIT_CHOICES,
        null=True,
        blank=True,
        help_text="Unit number (optional, mainly for Notes)"
    )

    # ── File storage ──────────────────────────────────────────────────────────
    file = models.FileField(upload_to=resource_upload_path)
    file_name = models.CharField(max_length=255, editable=False)
    file_size = models.PositiveBigIntegerField(editable=False, help_text="Size in bytes")
    file_type = models.CharField(max_length=100, editable=False, help_text="MIME type")

    # ── Ownership ─────────────────────────────────────────────────────────────
    uploaded_by = models.ForeignKey(
        'accounts.StaffProfile',
        on_delete=models.PROTECT,
        related_name='uploaded_resources'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'resources'
        ordering = ['-created_at']
        verbose_name = 'Resource'
        verbose_name_plural = 'Resources'
        indexes = [
            models.Index(fields=['department', 'subject']),
            models.Index(fields=['department', 'category']),
        ]

    def __str__(self):
        return f"{self.title} [{self.category}]"

    def save(self, *args, **kwargs):
        """Auto-populate file metadata on save."""
        if self.file:
            self.file_name = os.path.basename(self.file.name)
            if hasattr(self.file, 'size'):
                self.file_size = self.file.size
        super().save(*args, **kwargs)

    @property
    def file_size_display(self):
        """Human-readable file size."""
        size = self.file_size or 0
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
