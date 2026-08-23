"""
Resource upload form — restricted to teacher's assigned subjects only.
Includes all important fields with placeholders and helper text.
"""
from django import forms
from django.conf import settings
import os
from .models import Resource, ResourceCategory
from subjects.models import Subject, AcademicYear, TeacherSubject
from departments.models import Department


class ResourceUploadForm(forms.ModelForm):
    """
    Teachers upload a resource through this form.
    Subject choices are filtered to only show subjects assigned to the teacher.
    HOD/Super Admin can see all subjects in their department.
    """

    class Meta:
        model = Resource
        fields = [
            'category',
            'subject',
            'academic_year',
            'semester',
            'unit',
            'title',
            'description',
            'file',
        ]
        widgets = {
            'category': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_category',
            }),
            'subject': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_subject',
            }),
            'academic_year': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_academic_year',
            }),
            'semester': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_semester',
            }),
            'unit': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_unit',
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Data Structures Unit 1 Notes',
                'id': 'id_title',
                'maxlength': '300',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Brief description of this resource (optional)',
                'rows': 3,
                'id': 'id_description',
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control d-none',
                'id': 'id_file',
                'accept': ','.join(settings.ALLOWED_UPLOAD_EXTENSIONS),
            }),
        }
        labels = {
            'category': 'Resource Type',
            'subject': 'Subject',
            'academic_year': 'Academic Year',
            'semester': 'Semester',
            'unit': 'Unit (optional)',
            'title': 'Resource Title',
            'description': 'Description',
            'file': 'File',
        }
        help_texts = {
            'category': 'Select the type of resource you are uploading.',
            'subject': 'Only your assigned subjects are shown.',
            'unit': 'Unit number — mainly for Notes. Leave blank for other types.',
            'title': 'Give a clear, descriptive title.',
            'description': 'Add any relevant notes for students or colleagues.',
            'file': f'Allowed: PDF, DOC, DOCX, PPT, PPTX, XLS, XLSX, TXT, JPG, PNG, ZIP. Max {settings.MAX_UPLOAD_SIZE // (1024*1024)} MB.',
        }

    def __init__(self, *args, staff_profile=None, **kwargs):
        """
        staff_profile: the logged-in user's StaffProfile.
        Filters subject choices based on role:
          - Teacher → only assigned subjects
          - HOD/Super Admin → all active subjects in their department
        """
        super().__init__(*args, **kwargs)
        self.staff_profile = staff_profile

        if staff_profile:
            dept = staff_profile.department

            if staff_profile.is_teacher:
                # ── TEACHER: only assigned subjects ─────────────────────────
                assigned_ids = TeacherSubject.objects.filter(
                    teacher=staff_profile
                ).values_list('subject_id', flat=True)

                self.fields['subject'].queryset = Subject.objects.filter(
                    pk__in=assigned_ids,
                    status='active'
                ).select_related('department').order_by('semester', 'name')

            elif staff_profile.is_hod:
                # ── HOD: all subjects in their department ───────────────────
                self.fields['subject'].queryset = Subject.objects.filter(
                    department=dept,
                    status='active'
                ).select_related('department').order_by('semester', 'name')

            else:
                # ── Super Admin: all active subjects ────────────────────────
                self.fields['subject'].queryset = Subject.objects.filter(
                    status='active'
                ).select_related('department').order_by('department__code', 'name')

        # Always show only active categories and years
        self.fields['category'].queryset = ResourceCategory.objects.filter(is_active=True)
        self.fields['academic_year'].queryset = AcademicYear.objects.all().order_by('-start_year')

        # Make unit optional
        self.fields['unit'].required = False
        self.fields['description'].required = False
        self.fields['semester'].required = False

        # Add empty labels for selects
        self.fields['subject'].empty_label = '— Select Subject —'
        self.fields['category'].empty_label = '— Select Resource Type —'
        self.fields['academic_year'].empty_label = '— Select Academic Year —'
        self.fields['semester'].empty_label = '— Select Semester —'
        self.fields['unit'].empty_label = '— Select Unit (optional) —'

    def clean_file(self):
        """Validate file extension, MIME type, and size."""
        file = self.cleaned_data.get('file')
        if not file:
            raise forms.ValidationError("Please select a file to upload.")

        # Extension check
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
            allowed = ', '.join(settings.ALLOWED_UPLOAD_EXTENSIONS)
            raise forms.ValidationError(
                f"File type '{ext}' is not allowed. Allowed types: {allowed}"
            )

        # Size check
        if file.size > settings.MAX_UPLOAD_SIZE:
            max_mb = settings.MAX_UPLOAD_SIZE // (1024 * 1024)
            raise forms.ValidationError(
                f"File is too large. Maximum allowed size is {max_mb} MB."
            )

        return file

    def clean(self):
        """Cross-field validation: subject must belong to teacher's assigned list."""
        cleaned_data = super().clean()
        subject = cleaned_data.get('subject')
        staff = self.staff_profile

        if subject and staff and staff.is_teacher:
            assigned_ids = list(
                TeacherSubject.objects.filter(teacher=staff)
                .values_list('subject_id', flat=True)
            )
            if subject.pk not in assigned_ids:
                self.add_error(
                    'subject',
                    "You are not assigned to this subject. "
                    "Please contact your HOD to get assigned."
                )

        return cleaned_data


class ResourceEditForm(forms.ModelForm):
    """Allows editing metadata of an existing resource (title, description, category)."""

    class Meta:
        model = Resource
        fields = ['title', 'description', 'category', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Resource title',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Brief description (optional)',
                'rows': 3,
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'title': 'Resource Title',
            'description': 'Description',
            'category': 'Resource Type',
            'status': 'Status',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = ResourceCategory.objects.filter(is_active=True)
        self.fields['description'].required = False
