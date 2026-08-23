"""
Authentication and profile forms.
All forms include proper labels, placeholders, and helper text.
"""
from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User
from .models import StaffProfile


class LoginForm(AuthenticationForm):
    """Custom login form with styled fields."""

    username = forms.CharField(
        label="Username / Employee ID",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username or employee ID',
            'autofocus': True,
            'autocomplete': 'username',
        })
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
        })
    )


class StaffCreateForm(forms.ModelForm):
    """
    Super Admin uses this to create new staff accounts.
    Creates both User + StaffProfile in one form.
    """
    first_name = forms.CharField(
        label="First Name",
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Priya',
        })
    )
    last_name = forms.CharField(
        label="Last Name",
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Sharma',
        })
    )
    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. priya.sharma@college.edu',
        })
    )
    username = forms.CharField(
        label="Username",
        help_text="Used to log in. Cannot be changed later without admin.",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. priya.sharma',
        })
    )
    password = forms.CharField(
        label="Temporary Password",
        help_text="Staff should change this after first login.",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Set a temporary password',
        })
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Re-enter the password',
        })
    )

    class Meta:
        model = StaffProfile
        fields = ['employee_id', 'department', 'role', 'phone']
        widgets = {
            'employee_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. EMP001',
            }),
            'department': forms.Select(attrs={
                'class': 'form-select',
            }),
            'role': forms.Select(attrs={
                'class': 'form-select',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 9876543210',
            }),
        }
        labels = {
            'employee_id': 'Employee ID',
            'department': 'Department',
            'role': 'Role',
            'phone': 'Phone Number',
        }
        help_texts = {
            'employee_id': 'Unique college employee ID.',
            'department': 'Leave blank for Super Admin.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].initial = StaffProfile.ROLE_TEACHER
        self.fields['role'].help_text = 'Choose Teacher or HOD for a login account.'

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        confirm = cleaned.get('confirm_password')
        if password and confirm and password != confirm:
            self.add_error('confirm_password', 'Passwords do not match.')

        role = cleaned.get('role')
        department = cleaned.get('department')

        if role == StaffProfile.ROLE_SUPER_ADMIN and department:
            self.add_error('department', 'Super Admin is college-wide — do not assign a department.')

        if role in (StaffProfile.ROLE_HOD, StaffProfile.ROLE_TEACHER) and not department:
            self.add_error('department', 'Department is required for Teacher and HOD accounts.')

        return cleaned


class RegisterForm(StaffCreateForm):
    """
    Public self-registration from the login page.
    Only Teacher or HOD accounts can be created — never Super Admin.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].choices = [
            c for c in StaffProfile.ROLE_CHOICES if c[0] != StaffProfile.ROLE_SUPER_ADMIN
        ]
        self.fields['role'].initial = StaffProfile.ROLE_TEACHER
        self.fields['role'].help_text = 'Choose Teacher or HOD — you will be able to log in immediately.'
        self.fields['username'].help_text = 'Used to log in.'

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('role') == StaffProfile.ROLE_SUPER_ADMIN:
            self.add_error('role', 'Super Admin accounts cannot be created from the login page.')
        return cleaned


class StaffProfileUpdateForm(forms.ModelForm):
    """Staff members update their own profile. Sensitive fields are excluded."""

    first_name = forms.CharField(
        label="First Name",
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your first name',
        })
    )
    last_name = forms.CharField(
        label="Last Name",
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your last name',
        })
    )
    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your email address',
        })
    )

    class Meta:
        model = StaffProfile
        # Staff cannot change their own department/role/employee_id
        fields = ['phone', 'profile_photo']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 9876543210',
            }),
            'profile_photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/jpeg,image/png',
            }),
        }
        labels = {
            'phone': 'Phone Number',
            'profile_photo': 'Profile Photo',
        }
        help_texts = {
            'profile_photo': 'Upload JPG or PNG, max 2 MB.',
        }


class CustomPasswordChangeForm(PasswordChangeForm):
    """Styled password change form."""

    old_password = forms.CharField(
        label="Current Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your current password',
            'autocomplete': 'current-password',
        })
    )
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter a strong new password',
            'autocomplete': 'new-password',
        })
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Re-enter your new password',
            'autocomplete': 'new-password',
        })
    )


class StaffResetPasswordForm(forms.Form):
    """Super Admin sets a new password for a staff account."""
    new_password = forms.CharField(
        label="New Password",
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter a strong password (min 8 characters)',
            'autocomplete': 'new-password',
        })
    )
    confirm_password = forms.CharField(
        label="Confirm New Password",
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Re-enter the new password',
            'autocomplete': 'new-password',
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        pw = cleaned_data.get('new_password')
        confirm = cleaned_data.get('confirm_password')
        if pw and confirm and pw != confirm:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data
