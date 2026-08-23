"""
Excel import tests — valid files import, duplicates detected, missing
columns rejected, and cross-department import access is blocked.
"""
import io
import openpyxl
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from departments.models import Department
from accounts.models import StaffProfile
from students.models import Student
from .models import ExcelImport


def build_xlsx(rows, headers=None):
    """Return an in-memory .xlsx file as SimpleUploadedFile."""
    if headers is None:
        headers = ['Register Number', 'Student Name', 'Batch', 'Year', 'Semester', 'Section', 'Academic Year', 'Email']
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return SimpleUploadedFile('students.xlsx', buffer.read(),
                              content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


class ExcelImportTestCase(TestCase):
    def setUp(self):
        self.dept_cse = Department.objects.create(code='CSE', name='Computer Science')
        self.hod_cse = StaffProfile.objects.create(
            user=User.objects.create_user(username='excel_hod', password='password123'),
            employee_id='X-HOD', department=self.dept_cse, role=StaffProfile.ROLE_HOD,
        )

    def _mapping_post(self, excel_import, mapping=None):
        default = {
            'map_register_number': 'Register Number',
            'map_name': 'Student Name',
            'map_batch': 'Batch',
            'map_year': 'Year',
            'map_semester': 'Semester',
            'map_section': 'Section',
            'map_academic_year': 'Academic Year',
            'map_email': 'Email',
        }
        if mapping:
            default.update(mapping)
        return default

    def test_valid_excel_imports_students(self):
        client = Client()
        client.login(username='excel_hod', password='password123')

        excel_file = build_xlsx([
            ['REG001', 'Anil Kumar', '2023-2027', 4, 7, 'A', '2026-27', 'anil@college.edu'],
            ['REG002', 'Bhavana', '2023-2027', 4, 7, 'A', '2026-27', 'bhavana@college.edu'],
        ])

        response = client.post(reverse('excel_manager:import'), {'file': excel_file})
        self.assertEqual(response.status_code, 200)
        excel_import = ExcelImport.objects.latest('id')
        self.assertEqual(excel_import.status, ExcelImport.STATUS_PREVIEW)

        response = client.post(
            reverse('excel_manager:map', args=[excel_import.id]),
            self._mapping_post(excel_import),
        )
        self.assertEqual(response.status_code, 200)
        excel_import.refresh_from_db()
        self.assertEqual(excel_import.status, ExcelImport.STATUS_DONE)
        self.assertEqual(excel_import.imported_rows, 2)
        self.assertEqual(excel_import.invalid_rows, 0)
        self.assertEqual(excel_import.duplicate_rows, 0)
        self.assertEqual(Student.objects.filter(department=self.dept_cse).count(), 2)

    def test_duplicate_register_numbers_detected(self):
        client = Client()
        client.login(username='excel_hod', password='password123')

        excel_file = build_xlsx([
            ['REG001', 'Anil Kumar', '2023-2027', 4, 7, 'A', '2026-27', 'anil@college.edu'],
            ['REG001', 'Duplicate', '2023-2027', 4, 7, 'A', '2026-27', 'dup@college.edu'],
        ])
        client.post(reverse('excel_manager:import'), {'file': excel_file})
        excel_import = ExcelImport.objects.latest('id')
        response = client.post(
            reverse('excel_manager:map', args=[excel_import.id]),
            self._mapping_post(excel_import),
        )
        self.assertEqual(response.status_code, 200)
        excel_import.refresh_from_db()
        self.assertEqual(excel_import.imported_rows, 1)
        self.assertEqual(excel_import.duplicate_rows, 1)

    def test_invalid_rows_detected(self):
        client = Client()
        client.login(username='excel_hod', password='password123')

        excel_file = build_xlsx([
            ['REG001', 'Anil Kumar', '2023-2027', 4, 7, 'A', '2026-27', 'anil@college.edu'],
            ['', '', '2023-2027', 4, 7, 'A', '2026-27', ''],          # missing reg + name
            ['REG003', 'Bad Year', '2023-2027', 99, 7, 'A', '2026-27', ''],  # invalid year
        ])
        client.post(reverse('excel_manager:import'), {'file': excel_file})
        excel_import = ExcelImport.objects.latest('id')
        response = client.post(
            reverse('excel_manager:map', args=[excel_import.id]),
            self._mapping_post(excel_import),
        )
        self.assertEqual(response.status_code, 200)
        excel_import.refresh_from_db()
        self.assertEqual(excel_import.imported_rows, 1)
        self.assertEqual(excel_import.invalid_rows, 2)

    def test_missing_required_mapping_rejected(self):
        client = Client()
        client.login(username='excel_hod', password='password123')

        excel_file = build_xlsx([
            ['REG001', 'Anil Kumar', '2023-2027', 4, 7, 'A', '2026-27', 'anil@college.edu'],
        ])
        client.post(reverse('excel_manager:import'), {'file': excel_file})
        excel_import = ExcelImport.objects.latest('id')

        # Remove the register_number mapping → must be rejected
        mapping = self._mapping_post(excel_import)
        del mapping['map_register_number']
        response = client.post(
            reverse('excel_manager:map', args=[excel_import.id]),
            mapping,
        )
        self.assertNotEqual(response.status_code, 200)
        excel_import.refresh_from_db()
        self.assertNotEqual(excel_import.status, ExcelImport.STATUS_DONE)
        self.assertEqual(Student.objects.count(), 0)

    def test_invalid_file_type_rejected(self):
        client = Client()
        client.login(username='excel_hod', password='password123')
        bad_file = SimpleUploadedFile('notes.txt', b'not an excel file', content_type='text/plain')
        response = client.post(reverse('excel_manager:import'), {'file': bad_file})
        self.assertRedirects(response, reverse('excel_manager:import'))
        self.assertEqual(ExcelImport.objects.count(), 0)

    def test_cross_department_excel_import_blocked(self):
        """A CSE HOD must not be able to process an import belonging to ECE."""
        dept_ece = Department.objects.create(code='ECE', name='Electronics')
        hod_ece = StaffProfile.objects.create(
            user=User.objects.create_user(username='excel_hod_ece', password='password123'),
            employee_id='X-HOD-ECE', department=dept_ece, role=StaffProfile.ROLE_HOD,
        )

        client = Client()
        client.login(username='excel_hod', password='password123')
        excel_file = build_xlsx([['REG001', 'Anil', '2023-2027', 4, 7, 'A', '2026-27', 'a@b.c']])
        client.post(reverse('excel_manager:import'), {'file': excel_file})
        excel_import = ExcelImport.objects.latest('id')

        # Assign that import to ECE
        excel_import.department = dept_ece
        excel_import.save()

        response = client.post(
            reverse('excel_manager:map', args=[excel_import.id]),
            self._mapping_post(excel_import),
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Student.objects.count(), 0)
