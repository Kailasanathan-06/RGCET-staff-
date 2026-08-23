"""
Excel Import models — tracks every student Excel upload with its result.
Column mapping is stored as JSON so staff can re-map without code changes.
"""
import os
import uuid
from django.db import models
from django.utils import timezone
from departments.models import Department


def excel_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    dept_code = instance.department.code if instance.department else 'general'
    return f"excel_imports/{dept_code}/{unique_name}"


class ExcelImport(models.Model):
    """
    Tracks an Excel student import operation from upload → result.
    column_mapping stores staff's manual column-to-field mapping as JSON.
    error_log stores per-row errors for display after processing.
    """
    STATUS_PENDING = 'PENDING'
    STATUS_PREVIEW = 'PREVIEW'
    STATUS_PROCESSING = 'PROCESSING'
    STATUS_DONE = 'DONE'
    STATUS_FAILED = 'FAILED'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PREVIEW, 'Awaiting Column Mapping'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_DONE, 'Completed'),
        (STATUS_FAILED, 'Failed'),
    ]

    uploaded_by = models.ForeignKey(
        'accounts.StaffProfile',
        on_delete=models.PROTECT,
        related_name='excel_imports'
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='excel_imports'
    )

    file = models.FileField(upload_to=excel_upload_path)
    original_filename = models.CharField(max_length=255)

    # ── Mapping & Results ─────────────────────────────────────────────────────
    # Stored as JSON: {"register_number": "Reg No", "name": "Student Name", ...}
    column_mapping = models.JSONField(
        null=True,
        blank=True,
        help_text="Maps system field names to Excel column headers"
    )
    # Per-row errors: [{"row": 3, "error": "Duplicate register number"}, ...]
    error_log = models.JSONField(null=True, blank=True)

    # ── Counters ──────────────────────────────────────────────────────────────
    total_rows = models.PositiveIntegerField(default=0)
    imported_rows = models.PositiveIntegerField(default=0)
    duplicate_rows = models.PositiveIntegerField(default=0)
    invalid_rows = models.PositiveIntegerField(default=0)

    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )
    created_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'excel_imports'
        ordering = ['-created_at']
        verbose_name = 'Excel Import'
        verbose_name_plural = 'Excel Imports'

    def __str__(self):
        return f"{self.original_filename} — {self.department} [{self.status}]"

    @property
    def success_rate(self):
        if self.total_rows == 0:
            return 0
        return round((self.imported_rows / self.total_rows) * 100, 1)
