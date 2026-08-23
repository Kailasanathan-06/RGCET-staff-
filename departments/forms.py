"""
Department forms — clean labeled fields for admin use.
"""
from django import forms
from .models import Department


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['code', 'name', 'description', 'status']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. CSE',
                'maxlength': '20',
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Computer Science and Engineering',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Short description of the department (optional)',
                'rows': 3,
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'code': 'Department Code',
            'name': 'Department Name',
            'description': 'Description',
            'status': 'Status',
        }
        help_texts = {
            'code': 'Short unique code — used in file paths and references.',
            'name': 'Official full department name.',
        }
