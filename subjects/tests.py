from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from departments.models import Department
from accounts.models import StaffProfile
from subjects.models import Subject, AcademicYear, Regulation, TeacherSubject


class CourseCreateTestCase(TestCase):
    """Tests for the Add Course feature (create subject + upload files)."""

    def setUp(self):
        self.dept_cse = Department.objects.create(code='CSE', name='Computer Science')
        self.dept_ece = Department.objects.create(code='ECE', name='Electronics')
        self.year = AcademicYear.objects.create(
            name='2026-27', start_year=2026, end_year=2027, is_current=True
        )
        self.reg = Regulation.objects.create(code='R2025', name='Regulation 2025')

        self.teacher = StaffProfile.objects.create(
            user=User.objects.create_user(username='teacher_cse', password='password123'),
            employee_id='T-CSE', department=self.dept_cse, role=StaffProfile.ROLE_TEACHER,
        )
        self.hod = StaffProfile.objects.create(
            user=User.objects.create_user(username='hod_cse', password='password123'),
            employee_id='HOD-CSE', department=self.dept_cse, role=StaffProfile.ROLE_HOD,
        )
        self.admin = StaffProfile.objects.create(
            user=User.objects.create_user(
                username='rootadmin', password='password123', is_staff=True, is_superuser=True
            ),
            employee_id='SUPER-01', role=StaffProfile.ROLE_SUPER_ADMIN,
        )

    def _post_course(self, client, code='CS310', department=None, files=None):
        department = department or self.dept_cse.id
        syllabus = SimpleUploadedFile('syllabus.pdf', b'syllabus content', content_type='application/pdf')
        qp = SimpleUploadedFile('qp.pdf', b'qp content', content_type='application/pdf')
        payload = {
            'code': code,
            'name': 'New Course',
            'department': department,
            'academic_year': self.year.id,
            'regulation': self.reg.id,
            'semester': 3,
            'credits': 4,
            'syllabus_files': syllabus,
            'question_paper_files': qp,
        }
        payload.update(files or {})
        return client.post(reverse('subjects:add_course'), payload)

    def test_unauthenticated_user_redirected_to_login(self):
        response = Client().get(reverse('subjects:add_course'))
        self.assertEqual(response.status_code, 302)

    def test_teacher_can_access_add_course_page(self):
        client = Client()
        client.login(username='teacher_cse', password='password123')
        response = client.get(reverse('subjects:add_course'))
        self.assertEqual(response.status_code, 200)

    def test_hod_can_access_add_course_page(self):
        client = Client()
        client.login(username='hod_cse', password='password123')
        response = client.get(reverse('subjects:add_course'))
        self.assertEqual(response.status_code, 200)

    def test_super_admin_can_access_add_course_page(self):
        client = Client()
        client.login(username='rootadmin', password='password123')
        response = client.get(reverse('subjects:add_course'))
        self.assertEqual(response.status_code, 200)

    def test_teacher_creates_course_with_files(self):
        client = Client()
        client.login(username='teacher_cse', password='password123')
        response = self._post_course(client)
        self.assertEqual(response.status_code, 302)

        subject = Subject.objects.get(code='CS310')
        self.assertEqual(subject.department, self.dept_cse)
        self.assertTrue(
            TeacherSubject.objects.filter(teacher=self.teacher, subject=subject).exists()
        )
        self.assertEqual(subject.resources.count(), 2)
        categories = set(subject.resources.values_list('category__slug', flat=True))
        self.assertEqual(categories, {'syllabus', 'question-papers'})

    def test_teacher_cannot_create_course_in_other_department(self):
        client = Client()
        client.login(username='teacher_cse', password='password123')
        response = self._post_course(client, code='EE310', department=self.dept_ece.id)
        self.assertFalse(Subject.objects.filter(code='EE310').exists())
        self.assertEqual(response.status_code, 200)

    def test_super_admin_can_create_course(self):
        client = Client()
        client.login(username='rootadmin', password='password123')
        response = self._post_course(client)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Subject.objects.filter(code='CS310').exists())

    def test_invalid_file_type_rejected(self):
        client = Client()
        client.login(username='teacher_cse', password='password123')
        bad = SimpleUploadedFile('malware.exe', b'x', content_type='application/octet-stream')
        response = self._post_course(client, files={'notes_files': bad})
        self.assertFalse(Subject.objects.filter(code='CS310').exists())
        self.assertEqual(response.status_code, 200)

    def test_duplicate_subject_code_rejected(self):
        Subject.objects.create(
            code='CS310', name='Existing', department=self.dept_cse,
            academic_year=self.year, regulation=self.reg, semester=3,
        )
        client = Client()
        client.login(username='teacher_cse', password='password123')
        response = self._post_course(client)
        self.assertEqual(Subject.objects.filter(code='CS310').count(), 1)
        self.assertEqual(response.status_code, 200)
