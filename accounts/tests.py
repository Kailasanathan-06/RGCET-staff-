from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from departments.models import Department
from accounts.models import StaffProfile
from subjects.models import Subject, AcademicYear, TeacherSubject, Regulation
from resources.models import Resource, ResourceCategory
from students.models import Student


class SecurityIsolationTestCase(TestCase):
    """
    Core security audit test cases.
    Verifies that CSE teachers can NEVER read ECE students, resources, or files.
    """

    def setUp(self):
        # 1. Create Departments
        self.dept_cse = Department.objects.create(code='CSE', name='Computer Science')
        self.dept_ece = Department.objects.create(code='ECE', name='Electronics')

        # 2. Create Regulations & Years
        self.year = AcademicYear.objects.create(name='2026-27', start_year=2026, end_year=2027, is_current=True)
        self.reg = Regulation.objects.create(code='R2025', name='Regulation 2025')

        # 3. Create Subjects
        self.subject_cse = Subject.objects.create(
            code='CS301', name='Data Structures', department=self.dept_cse,
            academic_year=self.year, regulation=self.reg, semester=3
        )
        self.subject_ece = Subject.objects.create(
            code='EC301', name='Microprocessors', department=self.dept_ece,
            academic_year=self.year, regulation=self.reg, semester=3
        )

        # 4. Create Users (Teachers)
        self.user_cse = User.objects.create_user(username='teacher_cse', password='password123')
        self.profile_cse = StaffProfile.objects.create(
            user=self.user_cse, employee_id='CSE01', department=self.dept_cse, role=StaffProfile.ROLE_TEACHER
        )

        self.user_ece = User.objects.create_user(username='teacher_ece', password='password123')
        self.profile_ece = StaffProfile.objects.create(
            user=self.user_ece, employee_id='ECE01', department=self.dept_ece, role=StaffProfile.ROLE_TEACHER
        )

        # 5. Assign subjects to teachers
        TeacherSubject.objects.create(teacher=self.profile_cse, subject=self.subject_cse, academic_year=self.year)
        TeacherSubject.objects.create(teacher=self.profile_ece, subject=self.subject_ece, academic_year=self.year)

        # 6. Create Resource Categories
        self.cat_notes = ResourceCategory.objects.create(name='Notes', slug='notes')

        # 7. Create Resources
        fake_file_cse = SimpleUploadedFile("ds_notes.pdf", b"CSE file content", content_type="application/pdf")
        self.resource_cse = Resource.objects.create(
            title="DS Unit 1 Notes", department=self.dept_cse, subject=self.subject_cse,
            category=self.cat_notes, academic_year=self.year, file=fake_file_cse,
            uploaded_by=self.profile_cse, status=Resource.STATUS_ACTIVE
        )

        fake_file_ece = SimpleUploadedFile("mp_notes.pdf", b"ECE file content", content_type="application/pdf")
        self.resource_ece = Resource.objects.create(
            title="MP Unit 1 Notes", department=self.dept_ece, subject=self.subject_ece,
            category=self.cat_notes, academic_year=self.year, file=fake_file_ece,
            uploaded_by=self.profile_ece, status=Resource.STATUS_ACTIVE
        )

        # 8. Create Students
        self.student_cse = Student.objects.create(
            register_number="REG-CSE-01", name="Anil Kumar", department=self.dept_cse,
            batch="2023-2027", academic_year="2026-27", year=4, semester=7, section="A"
        )
        self.student_ece = Student.objects.create(
            register_number="REG-ECE-01", name="Suresh Babu", department=self.dept_ece,
            batch="2023-2027", academic_year="2026-27", year=4, semester=7, section="A"
        )

    def test_cse_teacher_access_cse_resource_allowed(self):
        """CSE teacher should access CSE resource details page successfully."""
        client = Client()
        client.login(username='teacher_cse', password='password123')
        response = client.get(reverse('resources:detail', args=[self.resource_cse.id]))
        self.assertEqual(response.status_code, 200)

    def test_cse_teacher_access_ece_resource_blocked(self):
        """CSE teacher attempting to view ECE resource details must get 403 Forbidden."""
        client = Client()
        client.login(username='teacher_cse', password='password123')
        response = client.get(reverse('resources:detail', args=[self.resource_ece.id]))
        self.assertEqual(response.status_code, 403)

    def test_cse_teacher_download_ece_file_blocked(self):
        """CSE teacher attempting to download ECE file must get 403 Forbidden."""
        client = Client()
        client.login(username='teacher_cse', password='password123')
        response = client.get(reverse('resources:download', args=[self.resource_ece.id]))
        self.assertEqual(response.status_code, 403)

    def test_cse_teacher_view_ece_student_blocked(self):
        """CSE teacher attempting to view ECE student details must get 403 Forbidden."""
        client = Client()
        client.login(username='teacher_cse', password='password123')
        response = client.get(reverse('students:detail', args=[self.student_ece.id]))
        self.assertEqual(response.status_code, 403)

    def test_ece_teacher_access_ece_resource_allowed(self):
        """ECE teacher should access ECE resource details page successfully."""
        client = Client()
        client.login(username='teacher_ece', password='password123')
        response = client.get(reverse('resources:detail', args=[self.resource_ece.id]))
        self.assertEqual(response.status_code, 200)

    def test_ece_teacher_access_cse_resource_blocked(self):
        """ECE teacher attempting to view CSE resource details must get 403 Forbidden."""
        client = Client()
        client.login(username='teacher_ece', password='password123')
        response = client.get(reverse('resources:detail', args=[self.resource_cse.id]))
        self.assertEqual(response.status_code, 403)


class HODAndSuperAdminAccessTestCase(TestCase):
    """HOD sees only their own department; Super Admin sees everything."""

    def setUp(self):
        self.dept_cse = Department.objects.create(code='CSE', name='Computer Science')
        self.dept_ece = Department.objects.create(code='ECE', name='Electronics')
        self.year = AcademicYear.objects.create(name='2026-27', start_year=2026, end_year=2027, is_current=True)
        self.reg = Regulation.objects.create(code='R2025', name='Regulation 2025')

        self.subject_cse = Subject.objects.create(
            code='CS301', name='Data Structures', department=self.dept_cse,
            academic_year=self.year, regulation=self.reg, semester=3
        )
        self.subject_ece = Subject.objects.create(
            code='EC301', name='Microprocessors', department=self.dept_ece,
            academic_year=self.year, regulation=self.reg, semester=3
        )

        self.cat_notes = ResourceCategory.objects.create(name='Notes', slug='notes')

        self.fake_cse = SimpleUploadedFile("ds.pdf", b"cse", content_type="application/pdf")
        self.fake_ece = SimpleUploadedFile("mp.pdf", b"ece", content_type="application/pdf")

        # HOD CSE
        self.hod_cse = StaffProfile.objects.create(
            user=User.objects.create_user(username='hod_cse', password='password123'),
            employee_id='HOD-CSE', department=self.dept_cse, role=StaffProfile.ROLE_HOD,
        )
        # HOD ECE
        self.hod_ece = StaffProfile.objects.create(
            user=User.objects.create_user(username='hod_ece', password='password123'),
            employee_id='HOD-ECE', department=self.dept_ece, role=StaffProfile.ROLE_HOD,
        )
        # Super Admin
        self.super_admin = StaffProfile.objects.create(
            user=User.objects.create_user(
                username='rootadmin', password='password123',
                is_staff=True, is_superuser=True,
            ),
            employee_id='SUPER-01', role=StaffProfile.ROLE_SUPER_ADMIN,
        )

        self.resource_cse = Resource.objects.create(
            title="CSE Notes", department=self.dept_cse, subject=self.subject_cse,
            category=self.cat_notes, academic_year=self.year, file=self.fake_cse,
            uploaded_by=self.hod_cse,
        )
        self.resource_ece = Resource.objects.create(
            title="ECE Notes", department=self.dept_ece, subject=self.subject_ece,
            category=self.cat_notes, academic_year=self.year, file=self.fake_ece,
            uploaded_by=self.hod_ece,
        )

        self.student_cse = Student.objects.create(
            register_number="CSE-001", name="A", department=self.dept_cse,
            batch="2023-2027", academic_year="2026-27", year=4, semester=7, section="A",
        )
        self.student_ece = Student.objects.create(
            register_number="ECE-001", name="B", department=self.dept_ece,
            batch="2023-2027", academic_year="2026-27", year=4, semester=7, section="A",
        )

    def test_hod_cse_own_resource_allowed(self):
        client = Client()
        client.login(username='hod_cse', password='password123')
        self.assertEqual(client.get(reverse('resources:detail', args=[self.resource_cse.id])).status_code, 200)

    def test_hod_cse_other_department_resource_blocked(self):
        client = Client()
        client.login(username='hod_cse', password='password123')
        self.assertEqual(client.get(reverse('resources:detail', args=[self.resource_ece.id])).status_code, 403)

    def test_hod_cse_other_department_student_blocked(self):
        client = Client()
        client.login(username='hod_cse', password='password123')
        self.assertEqual(client.get(reverse('students:detail', args=[self.student_ece.id])).status_code, 403)

    def test_hod_cse_other_department_download_blocked(self):
        client = Client()
        client.login(username='hod_cse', password='password123')
        self.assertEqual(client.get(reverse('resources:download', args=[self.resource_ece.id])).status_code, 403)

    def test_super_admin_access_all_departments(self):
        client = Client()
        client.login(username='rootadmin', password='password123')
        self.assertEqual(client.get(reverse('resources:detail', args=[self.resource_cse.id])).status_code, 200)
        self.assertEqual(client.get(reverse('resources:detail', args=[self.resource_ece.id])).status_code, 200)
        self.assertEqual(client.get(reverse('students:detail', args=[self.student_cse.id])).status_code, 200)
        self.assertEqual(client.get(reverse('students:detail', args=[self.student_ece.id])).status_code, 200)

    def test_hod_cannot_manage_other_department_subjects(self):
        """HOD creating a subject for another department must be blocked."""
        client = Client()
        client.login(username='hod_cse', password='password123')
        response = client.post(reverse('subjects:add'), {
            'code': 'EC999', 'name': 'Hacked Subject', 'department': self.dept_ece.id,
            'academic_year': self.year.id, 'regulation': self.reg.id,
            'semester': 3, 'credits': 3, 'status': 'active',
        })
        self.assertFalse(Subject.objects.filter(code='EC999').exists())

    def test_teacher_cannot_access_unassigned_subject_resource(self):
        """A teacher assigned to CSE must be blocked (403) from a CSE resource
        that belongs to a subject they are NOT assigned to."""
        cse_teacher = StaffProfile.objects.create(
            user=User.objects.create_user(username='t_cse', password='password123'),
            employee_id='T-CSE', department=self.dept_cse, role=StaffProfile.ROLE_TEACHER,
        )
        # Assign teacher to subject_cse only. resource_ece is in ECE dept anyway.
        TeacherSubject.objects.create(teacher=cse_teacher, subject=self.subject_cse, academic_year=self.year)

        # Create a CSE resource on a subject the teacher is NOT assigned to
        other_cse_subject = Subject.objects.create(
            code='CS399', name='AI', department=self.dept_cse,
            academic_year=self.year, regulation=self.reg, semester=6,
        )
        other_resource = Resource.objects.create(
            title="AI Notes", department=self.dept_cse, subject=other_cse_subject,
            category=self.cat_notes, academic_year=self.year, file=self.fake_cse,
            uploaded_by=self.hod_cse,
        )

        client = Client()
        client.login(username='t_cse', password='password123')
        self.assertEqual(client.get(reverse('resources:detail', args=[other_resource.id])).status_code, 403)
        self.assertEqual(client.get(reverse('resources:download', args=[other_resource.id])).status_code, 403)

    def test_deactivated_account_cannot_login(self):
        client = Client()
        client.login(username='hod_cse', password='password123')
        self.hod_cse.status = StaffProfile.STATUS_INACTIVE
        self.hod_cse.save()
        # Login attempt on deactivated account
        login_client = Client()
        response = login_client.post(reverse('accounts:login'), {
            'username': 'hod_cse', 'password': 'password123',
        })
        self.assertIn(b'deactivated', response.content.lower())

    def test_department_management_super_admin_only(self):
        """Teachers/HODs must be blocked from department management pages."""
        client = Client()
        client.login(username='hod_cse', password='password123')
        self.assertEqual(client.get(reverse('departments:list')).status_code, 403)

        client = Client()
        client.login(username='rootadmin', password='password123')
        self.assertEqual(client.get(reverse('departments:list')).status_code, 200)
