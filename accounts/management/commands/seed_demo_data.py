"""
Seed the database with the full demo/starting dataset for a college.

Creates (idempotently — existing records are left untouched):
    - Academic years (2024-25 .. 2027-28)
    - Regulations (R2019, R2021, R2023)
    - Departments (CSE, IT, ECE, EEE, MECH, CIVIL, AIDS, AIML)
    - Resource categories (Notes, Question Papers, Lab Manuals, ...)
    - Staff accounts: 1 Super Admin, 1 HOD + 2 Teachers per department
    - Subjects per department
    - Teacher→Subject assignments
    - A small sample of students for the first two departments

Usage:
    python manage.py seed_demo_data [--password <pw>]
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction

from departments.models import Department
from accounts.models import StaffProfile
from subjects.models import AcademicYear, Regulation, Subject, TeacherSubject
from resources.models import ResourceCategory
from students.models import Student


DEFAULT_PASSWORD = 'RGCET@2026'

DEPARTMENTS = [
    ('CSE', 'Computer Science and Engineering'),
    ('IT', 'Information Technology'),
    ('ECE', 'Electronics and Communication Engineering'),
    ('EEE', 'Electrical and Electronics Engineering'),
    ('MECH', 'Mechanical Engineering'),
    ('CIVIL', 'Civil Engineering'),
    ('AIDS', 'Artificial Intelligence and Data Science'),
    ('AIML', 'Artificial Intelligence and Machine Learning'),
]

ACADEMIC_YEARS = ['2024-25', '2025-26', '2026-27', '2027-28']

REGULATIONS = [
    ('R2019', 'Regulation 2019'),
    ('R2021', 'Regulation 2021'),
    ('R2023', 'Regulation 2023'),
]

RESOURCE_CATEGORIES = [
    ('Notes', 'notes', 'Unit and lecture notes (PDF, PPT, DOCX)'),
    ('Question Papers', 'question-papers', 'Internal and model question papers'),
    ('Previous Year Question Papers', 'previous-year-question-papers', 'Past university question papers'),
    ('Internal Exam Materials', 'internal-exam-materials', 'Internal assessment preparation materials'),
    ('Lab Manuals', 'lab-manuals', 'Lab manuals and experiment guides'),
    ('Assignments', 'assignments', 'Assignment questions, instructions and solutions'),
    ('Study Materials', 'study-materials', 'General study material and reference books'),
    ('Syllabus', 'syllabus', 'Syllabus documents for the current regulation'),
]

# CSE subjects: (code, name, semester, credits)
SUBJECTS = {
    'CSE': [
        ('CS3301', 'Data Structures and Algorithms', 3, 4),
        ('CS3402', 'Database Management Systems', 4, 4),
        ('CS3501', 'Operating Systems', 5, 4),
        ('CS3602', 'Computer Networks', 6, 4),
        ('CS3701', 'Software Engineering', 7, 3),
    ],
    'IT': [
        ('IT3401', 'Data Warehousing', 4, 3),
        ('IT3501', 'Web Technologies', 5, 3),
        ('IT3602', 'Cloud Computing', 6, 3),
    ],
    'ECE': [
        ('EC3301', 'Microprocessors and Microcontrollers', 3, 4),
        ('EC3402', 'Digital Signal Processing', 4, 4),
        ('EC3501', 'VLSI Design', 5, 4),
    ],
    'EEE': [
        ('EE3301', 'Power Systems I', 3, 4),
        ('EE3402', 'Electrical Machines II', 4, 4),
    ],
    'MECH': [
        ('ME3301', 'Thermodynamics', 3, 4),
        ('ME3402', 'Fluid Mechanics', 4, 4),
    ],
    'AIDS': [
        ('AD3301', 'Machine Learning Fundamentals', 3, 4),
        ('AD3402', 'Data Visualization', 4, 3),
    ],
    'AIML': [
        ('AI3301', 'Artificial Intelligence', 3, 4),
        ('AI3402', 'Neural Networks', 4, 4),
    ],
}

SAMPLE_STUDENTS = {
    'CSE': [
        ('21CS001', 'Anil Kumar', '2023-2027', 4, 7, 'A'),
        ('21CS002', 'Bhavana Reddy', '2023-2027', 4, 7, 'A'),
        ('21CS003', 'Charu Dev', '2023-2027', 4, 7, 'B'),
        ('21CS004', 'Dinesh Rao', '2023-2027', 4, 7, 'B'),
        ('21CS005', 'Eswari Priya', '2023-2027', 4, 7, 'A'),
        ('22CS011', 'Farhan Shaik', '2022-2026', 3, 5, 'A'),
        ('22CS012', 'Gayatri Devi', '2022-2026', 3, 5, 'B'),
    ],
    'ECE': [
        ('21EC001', 'Harish Babu', '2023-2027', 4, 7, 'A'),
        ('21EC002', 'Ishita Sen', '2023-2027', 4, 7, 'A'),
        ('22EC011', 'Jagan Mohan', '2022-2026', 3, 5, 'B'),
    ],
}


class Command(BaseCommand):
    help = 'Seed the database with starting college data and staff accounts.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            default=DEFAULT_PASSWORD,
            help=f'Password for all created accounts (default: {DEFAULT_PASSWORD})',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        password = options['password']
        created = []

        # ── Academic Years ───────────────────────────────────────────────────
        for i, name in enumerate(ACADEMIC_YEARS):
            start_part, end_part = name.split('-')
            ay, was = AcademicYear.objects.get_or_create(
                name=name,
                defaults={
                    'start_year': int(start_part),
                    'end_year': 2000 + int(end_part),
                    'is_current': (name == '2026-27'),
                },
            )
            created.append(f"Academic Year: {ay.name} ({'created' if was else 'exists'})")

        # ── Regulations ──────────────────────────────────────────────────────
        for code, name in REGULATIONS:
            reg, was = Regulation.objects.get_or_create(code=code, defaults={'name': name})
            created.append(f"Regulation: {reg.code} ({'created' if was else 'exists'})")

        # ── Resource Categories ──────────────────────────────────────────────
        for order, (name, slug, desc) in enumerate(RESOURCE_CATEGORIES):
            cat, was = ResourceCategory.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'description': desc, 'sort_order': order},
            )
            created.append(f"Category: {cat.name} ({'created' if was else 'exists'})")

        # ── Departments ──────────────────────────────────────────────────────
        depts = {}
        for code, name in DEPARTMENTS:
            dept, was = Department.objects.get_or_create(code=code, defaults={'name': name})
            depts[code] = dept
            created.append(f"Department: {dept.code} — {dept.name} ({'created' if was else 'exists'})")

        # ── Users (Super Admin, HODs, Teachers) ─────────────────────────────
        credentials = []

        admin_user, was = self._create_user('admin', 'Super', 'Administrator', 'admin@college.edu',
                                            'RGCET-ADM', None, StaffProfile.ROLE_SUPER_ADMIN, password)
        credentials.append({'username': 'admin', 'password': password, 'name': 'Super Administrator',
                            'role': 'Super Admin', 'department': 'All'})
        created.append(f"User: admin ({'created' if was else 'exists'})")

        for code, _ in DEPARTMENTS:
            dept = depts[code]
            low = code.lower()

            # HOD
            hod_user, was = self._create_user(
                f'hod_{low}', 'Head', f'{code} HOD', f'hod.{low}@college.edu',
                f'RGCET-{code}-HOD', dept, StaffProfile.ROLE_HOD, password,
            )
            credentials.append({'username': f'hod_{low}', 'password': password,
                                'name': f'Head of {code}', 'role': 'HOD',
                                'department': code})
            created.append(f"User: hod_{low} ({'created' if was else 'exists'})")

            # Two teachers
            for i in (1, 2):
                t_user, was = self._create_user(
                    f'{low}_teacher{i}', f'{code}', f'Teacher {i}', f'{low}.teacher{i}@college.edu',
                    f'RGCET-{code}-T{i}', dept, StaffProfile.ROLE_TEACHER, password,
                )
                credentials.append({'username': f'{low}_teacher{i}', 'password': password,
                                    'name': f'{code} Teacher {i}', 'role': 'Teacher',
                                    'department': code})
                created.append(f"User: {low}_teacher{i} ({'created' if was else 'exists'})")

        # ── Subjects + teacher assignments ───────────────────────────────────
        current_year = AcademicYear.objects.get(name='2026-27')
        reg = Regulation.objects.get(code='R2021')

        for code, subjects in SUBJECTS.items():
            dept = depts[code]
            for subj_code, name, sem, credits in subjects:
                subject, was = Subject.objects.get_or_create(
                    code=subj_code,
                    department=dept,
                    academic_year=current_year,
                    defaults={
                        'name': name,
                        'semester': sem,
                        'credits': credits,
                        'regulation': reg,
                    },
                )
                created.append(f"Subject: {subject.code} — {subject.name} ({'created' if was else 'exists'})")

                # Assign department teachers to each subject
                hod = StaffProfile.objects.filter(department=dept, role=StaffProfile.ROLE_HOD).first()
                teachers = list(StaffProfile.objects.filter(
                    department=dept, role=StaffProfile.ROLE_TEACHER)[:2])

                for assignee in [hod] + teachers:
                    if assignee is None:
                        continue
                    TeacherSubject.objects.get_or_create(
                        teacher=assignee,
                        subject=subject,
                        academic_year=current_year,
                        defaults={'assigned_by': StaffProfile.objects.filter(
                            role=StaffProfile.ROLE_SUPER_ADMIN).first()},
                    )
                created.append(f"Assignments for {subject.code}: HOD + {len(teachers)} teacher(s)")

        # ── Sample students ──────────────────────────────────────────────────
        for code, students in SAMPLE_STUDENTS.items():
            dept = depts[code]
            for reg_no, name, batch, year, sem, section in students:
                student, was = Student.objects.get_or_create(
                    register_number=reg_no,
                    defaults={
                        'name': name,
                        'department': dept,
                        'batch': batch,
                        'academic_year': '2026-27',
                        'year': year,
                        'semester': sem,
                        'section': section,
                        'status': Student.STATUS_ACTIVE,
                    },
                )
                created.append(f"Student: {student.register_number} ({'created' if was else 'exists'})")

        # ── Output ───────────────────────────────────────────────────────────
        created_count = len([c for c in created if 'created' in c])
        self.stdout.write(self.style.SUCCESS(f'\nSeed completed: {len(created)} records processed, '
                                             f'{created_count} newly created.'))
        self.stdout.write(self.style.SUCCESS(f'\nAll accounts use the password:  {password}\n'))
        self.stdout.write('-' * 70)
        self.stdout.write(f'{"Username":<18}{"Role":<14}{"Department":<12}Name')
        self.stdout.write('-' * 70)
        for c in credentials:
            self.stdout.write(f'{c["username"]:<18}{c["role"]:<14}{c["department"]:<12}{c["name"]}')

    def _create_user(self, username, first, last, email, emp_id, dept, role, password):
        """Create a User + StaffProfile pair if they don't exist."""
        was = False
        user = User.objects.filter(username=username).first()
        if user is None:
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first,
                last_name=last,
                email=email,
                is_staff=role == StaffProfile.ROLE_SUPER_ADMIN,
                is_superuser=role == StaffProfile.ROLE_SUPER_ADMIN,
            )
            was = True

        profile = StaffProfile.objects.filter(user=user).first()
        if profile is None:
            profile = StaffProfile.objects.create(
                user=user,
                employee_id=emp_id,
                department=dept,
                role=role,
                status=StaffProfile.STATUS_ACTIVE,
            )
            was = True
        return user, was
