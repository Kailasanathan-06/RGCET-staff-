"""
Subject forms — department choices restricted by role.
HOD can only create subjects in their own department.
"""
import os

from django import forms
from django.conf import settings
from .models import Subject, AcademicYear, Regulation
from departments.models import Department


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['code', 'name', 'department', 'academic_year', 'regulation', 'semester', 'credits', 'status']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. CS3301',
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Data Structures and Algorithms',
            }),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'academic_year': forms.Select(attrs={'class': 'form-select'}),
            'regulation': forms.Select(attrs={'class': 'form-select'}),
            'semester': forms.Select(attrs={'class': 'form-select'}),
            'credits': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 6}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'code': 'Subject Code',
            'name': 'Subject Name',
            'department': 'Department',
            'academic_year': 'Academic Year',
            'regulation': 'Regulation',
            'semester': 'Semester',
            'credits': 'Credits',
            'status': 'Status',
        }

    def __init__(self, *args, staff_profile=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.staff_profile = staff_profile

        self.fields['academic_year'].queryset = AcademicYear.objects.all().order_by('-start_year')
        self.fields['regulation'].queryset = Regulation.objects.filter(status='active')
        self.fields['regulation'].required = False
        self.fields['semester'].empty_label = '— Select Semester —'
        self.fields['department'].empty_label = '— Select Department —'

        # HOD: department is fixed to their own department
        if staff_profile and staff_profile.is_hod:
            self.fields['department'].queryset = Department.objects.filter(
                pk=staff_profile.department_id
            )
            self.fields['department'].empty_label = None
            if not self.instance.pk:
                self.fields['department'].initial = staff_profile.department_id

    def clean(self):
        cleaned_data = super().clean()
        staff = self.staff_profile
        department = cleaned_data.get('department')

        if staff and staff.is_hod and department is not None:
            if department.id != staff.department_id:
                self.add_error(
                    'department',
                    "You can only create subjects in your own department."
                )
        return cleaned_data


class MultipleFileInput(forms.ClearableFileInput):
    """File input that exposes every selected file (not just the last one)."""

    allow_multiple_selected = True

    def value_from_datadict(self, data, files, name):
        if not files:
            return None
        return files.getlist(name)


class MultipleFileField(forms.FileField):
    """A FileField that accepts more than one file from a single input."""

    widget = MultipleFileInput

    def clean(self, data, initial=None):
        if not data:
            return []
        if isinstance(data, (list, tuple)):
            return list(data)
        return [data]


class CourseForm(forms.ModelForm):
    """
    Combined "Add Course" form: create a new subject AND upload its
    syllabus, question papers and notes in a single step.
    Teachers/HODs can only add courses in their own department.
    """

    syllabus_files = MultipleFileField(
        label='Syllabus Documents',
        required=False,
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'multiple': True,
            'accept': '.pdf,.doc,.docx,.ppt,.pptx,.txt',
        }),
        help_text='Select one or more syllabus files (PDF/DOC/PPT).',
    )
    question_paper_files = MultipleFileField(
        label='Question Papers',
        required=False,
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'multiple': True,
            'accept': '.pdf,.doc,.docx,.ppt,.pptx,.txt',
        }),
        help_text='Select one or more question paper files (PDF/DOC).',
    )
    notes_files = MultipleFileField(
        label='Notes / Study Materials',
        required=False,
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'multiple': True,
            'accept': ','.join(settings.ALLOWED_UPLOAD_EXTENSIONS),
        }),
        help_text='Select one or more notes / study material files.',
    )

    class Meta:
        model = Subject
        fields = ['code', 'name', 'department', 'academic_year', 'regulation', 'semester', 'credits']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. CS3301',
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Data Structures and Algorithms',
            }),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'academic_year': forms.Select(attrs={'class': 'form-select'}),
            'regulation': forms.Select(attrs={'class': 'form-select'}),
            'semester': forms.Select(attrs={'class': 'form-select'}),
            'credits': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 6}),
        }
        labels = {
            'code': 'Course / Subject Code',
            'name': 'Course / Subject Name',
            'department': 'Department',
            'academic_year': 'Academic Year',
            'regulation': 'Regulation',
            'semester': 'Semester',
            'credits': 'Credits',
        }

    def __init__(self, *args, staff_profile=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.staff_profile = staff_profile

        self.fields['academic_year'].queryset = AcademicYear.objects.all().order_by('-start_year')
        self.fields['regulation'].queryset = Regulation.objects.filter(status='active')
        self.fields['regulation'].required = False
        self.fields['semester'].empty_label = '— Select Semester —'
        self.fields['department'].empty_label = '— Select Department —'

        # Teachers/HODs: department fixed to their own department
        if staff_profile and not staff_profile.is_super_admin:
            self.fields['department'].queryset = Department.objects.filter(
                pk=staff_profile.department_id
            )
            self.fields['department'].empty_label = None
            if not self.instance.pk:
                self.fields['department'].initial = staff_profile.department_id

    def _validate_upload(self, file):
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
            allowed = ', '.join(settings.ALLOWED_UPLOAD_EXTENSIONS)
            raise forms.ValidationError(
                f"File type '{ext}' is not allowed. Allowed types: {allowed}"
            )
        if file.size > settings.MAX_UPLOAD_SIZE:
            max_mb = settings.MAX_UPLOAD_SIZE // (1024 * 1024)
            raise forms.ValidationError(
                f"File is too large. Maximum allowed size is {max_mb} MB."
            )

    def _clean_file_field(self, field_name):
        files = self.cleaned_data.get(field_name) or []
        for file in files:
            self._validate_upload(file)
        return files

    def clean_syllabus_files(self):
        return self._clean_file_field('syllabus_files')

    def clean_question_paper_files(self):
        return self._clean_file_field('question_paper_files')

    def clean_notes_files(self):
        return self._clean_file_field('notes_files')

    def clean(self):
        cleaned_data = super().clean()
        staff = self.staff_profile
        department = cleaned_data.get('department')

        if staff and not staff.is_super_admin and department is not None:
            if department.id != staff.department_id:
                self.add_error(
                    'department',
                    "You can only add courses in your own department."
                )
        return cleaned_data
