import pandas as pd
import openpyxl
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from accounts.mixins import LoginAndActiveRequiredMixin, HODOrAboveMixin
from audit.models import AuditLog
from students.models import Student
from .models import ExcelImport


class ExcelUploadView(LoginAndActiveRequiredMixin, View):
    """
    Step 1: Upload Excel file.
    Step 2: Save metadata and render preview/column mapping screen.
    """
    def get(self, request):
        return render(request, 'excel_manager/import.html')

    def post(self, request):
        if 'file' not in request.FILES:
            messages.error(request, "Please select an Excel file.")
            return redirect('excel_manager:import')

        file = request.FILES['file']
        if not (file.name.endswith('.xlsx') or file.name.endswith('.xls') or file.name.endswith('.csv')):
            messages.error(request, "Invalid file format. Please upload an .xlsx, .xls, or .csv file.")
            return redirect('excel_manager:import')

        profile = request.user.profile
        dept = profile.department
        if not dept and not profile.is_super_admin:
            messages.error(request, "Staff profile is not associated with a department.")
            return redirect('dashboard:home')

        # Create import log record
        excel_import = ExcelImport.objects.create(
            uploaded_by=profile,
            department=dept,
            file=file,
            original_filename=file.name,
            status=ExcelImport.STATUS_PREVIEW
        )

        # Read headers of Excel
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(excel_import.file.path, nrows=5)
            else:
                df = pd.read_excel(excel_import.file.path, nrows=5)
            headers = list(df.columns)
        except Exception as e:
            excel_import.status = ExcelImport.STATUS_FAILED
            excel_import.error_log = {"error": f"Failed to read file headers: {str(e)}"}
            excel_import.save()
            messages.error(request, f"Could not read Excel file headers. Error: {e}")
            return redirect('excel_manager:import')

        fields = [
            ('register_number', 'Register Number (Required, Unique)'),
            ('name', 'Student Name (Required)'),
            ('email', 'Email Address (Optional)'),
            ('phone', 'Phone Number (Optional)'),
            ('batch', 'Batch e.g. 2023-2027 (Required)'),
            ('year', 'Year of Study (1-4) (Required)'),
            ('semester', 'Semester (1-8) (Required)'),
            ('section', 'Section e.g. A, B, C (Required)'),
            ('academic_year', 'Academic Year e.g. 2026-27 (Required)')
        ]

        suggested_map = {field: _suggest_header(field, headers) for field, _ in fields}

        return render(request, 'excel_manager/mapping.html', {
            'excel_import': excel_import,
            'headers': headers,
            'fields': fields,
            'suggested_map': suggested_map,
        })


def _suggest_header(field_name, headers):
    """Return the header that best matches a database field name (or '')."""
    lower = field_name.lower()
    candidates = {lower, lower.replace('_', ' '), lower.replace('_', ''), lower.replace('_', ' ')}
    for header in headers:
        hl = header.lower()
        if hl in candidates:
            return header
    if field_name == 'register_number':
        for header in headers:
            hl = header.lower()
            if 'reg' in hl or 'roll' in hl:
                return header
    if field_name == 'name':
        for header in headers:
            if 'name' in header.lower():
                return header
    return ''


class ExcelMapAndProcessView(LoginAndActiveRequiredMixin, View):
    """
    Step 3: Receive column mapping.
    Step 4: Validate rows, parse data, create Student records.
    Step 5: Render Summary.
    """
    def post(self, request, pk):
        excel_import = get_object_or_404(ExcelImport, pk=pk)
        profile = request.user.profile
        
        # Security isolation check
        if not profile.is_super_admin and excel_import.department != profile.department:
            raise PermissionDenied

        # Capture column mappings
        mapping = {}
        required_fields = ['register_number', 'name', 'batch', 'year', 'semester', 'section', 'academic_year']
        
        for field in required_fields + ['email', 'phone']:
            col = request.POST.get(f'map_{field}')
            if col:
                mapping[field] = col

        # Validate that all required fields are mapped
        missing_mappings = [f for f in required_fields if f not in mapping]
        if missing_mappings:
            messages.error(request, f"Please map all required columns. Missing: {', '.join(missing_mappings)}")
            return redirect('excel_manager:import')

        excel_import.column_mapping = mapping
        excel_import.status = ExcelImport.STATUS_PROCESSING
        excel_import.save()

        # Load file and process
        try:
            file_path = excel_import.file.path
            if excel_import.original_filename.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
        except Exception as e:
            excel_import.status = ExcelImport.STATUS_FAILED
            excel_import.error_log = {"error": f"Failed to load file for processing: {str(e)}"}
            excel_import.save()
            messages.error(request, f"Error processing file: {e}")
            return redirect('excel_manager:import')

        total_rows = len(df)
        imported = 0
        duplicates = 0
        invalid = 0
        errors = []

        df = df.where(pd.notnull(df), None)

        for index, row in df.iterrows():
            row_num = index + 2  # Excel row numbers start at 2 (excluding header)
            
            try:
                # Extract values using the mapped column names
                reg_num = str(row[mapping['register_number']]).strip() if row[mapping['register_number']] else ''
                name = str(row[mapping['name']]).strip() if row[mapping['name']] else ''
                batch = str(row[mapping['batch']]).strip() if row[mapping['batch']] else ''
                year_val = row[mapping['year']]
                sem_val = row[mapping['semester']]
                section = str(row[mapping['section']]).strip().upper() if row[mapping['section']] else ''
                academic_year = str(row[mapping['academic_year']]).strip() if row[mapping['academic_year']] else ''
                
                email = str(row[mapping.get('email')]).strip() if mapping.get('email') and row[mapping.get('email')] else ''
                phone = str(row[mapping.get('phone')]).strip() if mapping.get('phone') and row[mapping.get('phone')] else ''

                # Data Validation
                if not reg_num or not name or not batch or not year_val or not sem_val:
                    invalid += 1
                    errors.append({"row": row_num, "error": "Missing required fields."})
                    continue

                try:
                    year = int(year_val)
                    semester = int(sem_val)
                except ValueError:
                    invalid += 1
                    errors.append({"row": row_num, "error": f"Year '{year_val}' and Semester '{sem_val}' must be numeric."})
                    continue

                if year not in [1, 2, 3, 4] or semester not in range(1, 9):
                    invalid += 1
                    errors.append({"row": row_num, "error": f"Invalid range. Year: {year} (1-4), Semester: {semester} (1-8)"})
                    continue

                # Check duplicate register numbers in database
                if Student.objects.filter(register_number=reg_num).exists():
                    duplicates += 1
                    errors.append({"row": row_num, "error": f"Duplicate register number: {reg_num}"})
                    continue

                # Create the student
                Student.objects.create(
                    register_number=reg_num,
                    name=name,
                    email=email or None,
                    phone=phone or None,
                    department=excel_import.department,
                    batch=batch,
                    academic_year=academic_year,
                    year=year,
                    semester=semester,
                    section=section or None,
                    status=Student.STATUS_ACTIVE
                )
                imported += 1

            except Exception as e:
                invalid += 1
                errors.append({"row": row_num, "error": f"Unexpected error parsing row: {str(e)}"})

        # Update import stats
        excel_import.total_rows = total_rows
        excel_import.imported_rows = imported
        excel_import.duplicate_rows = duplicates
        excel_import.invalid_rows = invalid
        excel_import.error_log = errors
        excel_import.status = ExcelImport.STATUS_DONE
        excel_import.completed_at = timezone.now()
        excel_import.save()

        AuditLog.log(
            user=request.user,
            action=AuditLog.ACTION_EXCEL_IMPORT,
            description=f"Excel import completed: {imported} imported, {duplicates} duplicate, {invalid} invalid.",
            department=excel_import.department,
            ip_address=request.client_ip
        )

        return render(request, 'excel_manager/summary.html', {
            'excel_import': excel_import,
            'errors': errors
        })
