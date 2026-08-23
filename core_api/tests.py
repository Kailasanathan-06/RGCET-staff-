"""
REST API tests — verifies strict department isolation on every protected endpoint.
The API must never leak cross-department data, regardless of how the request
is crafted (IDs are guessed / modified).
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from departments.models import Department
from accounts.models import StaffProfile
from subjects.models import Subject, AcademicYear, Regulation, TeacherSubject
from resources.models import Resource, ResourceCategory
from students.models import Student


class APISecurityIsolationTestCase(TestCase):
    """CSE teacher using the REST API must never see ECE data."""

    def setUp(self):
        self.dept_cse = Department.objects.create(code='CSE', name='Computer Science')
        self.dept_ece = Department.objects.create(code='ECE', name='Electronics')
        self.year = AcademicYear.objects.create(name='2026-27', start_year=2026, end_year=2027, is_current=True)
        self.reg = Regulation.objects.create(code='R2025', name='Regulation 2025')

        self.subject_cse = Subject.objects.create(
            code='CS301', name='Data Structures', department=self.dept_cse,
            academic_year=self.year, regulation=self.reg, semester=3,
        )
        self.subject_ece = Subject.objects.create(
            code='EC301', name='Microprocessors', department=self.dept_ece,
            academic_year=self.year, regulation=self.reg, semester=3,
        )

        self.teacher_cse = StaffProfile.objects.create(
            user=User.objects.create_user(username='api_cse', password='password123'),
            employee_id='API-CSE', department=self.dept_cse, role=StaffProfile.ROLE_TEACHER,
        )
        self.teacher_ece = StaffProfile.objects.create(
            user=User.objects.create_user(username='api_ece', password='password123'),
            employee_id='API-ECE', department=self.dept_ece, role=StaffProfile.ROLE_TEACHER,
        )
        TeacherSubject.objects.create(teacher=self.teacher_cse, subject=self.subject_cse, academic_year=self.year)
        TeacherSubject.objects.create(teacher=self.teacher_ece, subject=self.subject_ece, academic_year=self.year)

        self.cat = ResourceCategory.objects.create(name='Notes', slug='notes')
        self.file_cse = SimpleUploadedFile("cse.pdf", b"cse", content_type="application/pdf")
        self.file_ece = SimpleUploadedFile("ece.pdf", b"ece", content_type="application/pdf")

        self.resource_cse = Resource.objects.create(
            title="CSE Notes", department=self.dept_cse, subject=self.subject_cse,
            category=self.cat, academic_year=self.year, file=self.file_cse,
            uploaded_by=self.teacher_cse,
        )
        self.resource_ece = Resource.objects.create(
            title="ECE Notes", department=self.dept_ece, subject=self.subject_ece,
            category=self.cat, academic_year=self.year, file=self.file_ece,
            uploaded_by=self.teacher_ece,
        )

        self.student_cse = Student.objects.create(
            register_number="STU-CSE-1", name="A", department=self.dept_cse,
            batch="2023-2027", academic_year="2026-27", year=4, semester=7, section="A",
        )
        self.student_ece = Student.objects.create(
            register_number="STU-ECE-1", name="B", department=self.dept_ece,
            batch="2023-2027", academic_year="2026-27", year=4, semester=7, section="A",
        )

    def _auth_client(self, username):
        client = Client()
        client.login(username=username, password='password123')
        return client

    def test_api_resource_list_is_department_scoped(self):
        client = self._auth_client('api_cse')
        response = client.get(reverse('api:resource-list'))
        self.assertEqual(response.status_code, 200)
        data = response.json().get('results')
        ids = [item['id'] for item in data]
        self.assertIn(self.resource_cse.id, ids)
        self.assertNotIn(self.resource_ece.id, ids)

    def test_api_cannot_retrieve_other_department_resource(self):
        client = self._auth_client('api_cse')
        response = client.get(reverse('api:resource-detail', args=[self.resource_ece.id]))
        self.assertEqual(response.status_code, 404)

    def test_api_cannot_download_other_department_resource(self):
        client = self._auth_client('api_cse')
        response = client.get(reverse('api:resource-download', args=[self.resource_ece.id]))
        self.assertEqual(response.status_code, 403)

    def test_api_can_download_own_department_resource(self):
        client = self._auth_client('api_cse')
        response = client.get(reverse('api:resource-download', args=[self.resource_cse.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'cse')

    def test_api_student_list_is_department_scoped(self):
        client = self._auth_client('api_cse')
        response = client.get(reverse('api:student-list'))
        self.assertEqual(response.status_code, 200)
        data = response.json().get('results')
        regs = [item['register_number'] for item in data]
        self.assertIn('STU-CSE-1', regs)
        self.assertNotIn('STU-ECE-1', regs)

    def test_api_cannot_retrieve_other_department_student(self):
        client = self._auth_client('api_cse')
        response = client.get(reverse('api:student-detail', args=[self.student_ece.id]))
        self.assertEqual(response.status_code, 404)

    def test_api_teacher_cannot_create_resource_for_other_department(self):
        client = self._auth_client('api_cse')
        response = client.post(reverse('api:resource-list'), {
            'title': 'Hacked',
            'subject': self.subject_ece.id,
            'category': self.cat.id,
            'academic_year': self.year.id,
            'semester': 3,
            'file': self.file_cse,
        }, format='multipart')
        self.assertIn(response.status_code, (403, 400))
        self.assertFalse(Resource.objects.filter(title='Hacked').exists())

    def test_api_unauthenticated_requests_blocked(self):
        client = Client()
        for url in [
            reverse('api:resource-list'),
            reverse('api:student-list'),
            reverse('api:subject-list'),
            reverse('api:department-list'),
        ]:
            response = client.get(url)
            self.assertIn(response.status_code, (401, 403))

    def test_api_subject_list_scoped_to_assignments(self):
        client = self._auth_client('api_cse')
        response = client.get(reverse('api:subject-list'))
        data = response.json().get('results')
        codes = [item['code'] for item in data]
        self.assertIn('CS301', codes)
        self.assertNotIn('EC301', codes)
