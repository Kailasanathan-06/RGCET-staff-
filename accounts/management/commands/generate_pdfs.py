"""
Generate the three project PDFs:
    - PROJECT_INFORMATION.pdf  (project overview, tech stack, architecture, security)
    - USER_CREDENTIALS.pdf     (seeded usernames, roles, departments and passwords)
    - RUNNING_COMMANDS.pdf     (all commands to set up, run and deploy)

Usage:
    python manage.py generate_pdfs [--out-dir <dir>]
"""
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph, Spacer, Table, TableStyle, SimpleDocTemplate
)
from accounts.models import StaffProfile
from accounts.management.commands.seed_demo_data import DEFAULT_PASSWORD

NAVY = colors.HexColor('#0F3460')
ACCENT = colors.HexColor('#E94560')
LIGHT = colors.HexColor('#F5F7FB')


class Command(BaseCommand):
    help = 'Generate PROJECT_INFORMATION.pdf, USER_CREDENTIALS.pdf and RUNNING_COMMANDS.pdf.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--out-dir', default=None,
            help='Output directory (default: project root).',
        )

    def handle(self, *args, **options):
        out_dir = options['out_dir'] or str(settings.BASE_DIR)
        os.makedirs(out_dir, exist_ok=True)

        project_pdf = os.path.join(out_dir, 'PROJECT_INFORMATION.pdf')
        users_pdf = os.path.join(out_dir, 'USER_CREDENTIALS.pdf')
        commands_pdf = os.path.join(out_dir, 'RUNNING_COMMANDS.pdf')

        self._build_project_pdf(project_pdf)
        self._build_users_pdf(users_pdf)
        self._build_commands_pdf(commands_pdf)

        self.stdout.write(self.style.SUCCESS(f'\nCreated: {project_pdf}'))
        self.stdout.write(self.style.SUCCESS(f'Created: {users_pdf}'))
        self.stdout.write(self.style.SUCCESS(f'Created: {commands_pdf}'))

    # -- Shared helpers -------------------------------------------------------
    @staticmethod
    def _styles():
        base = getSampleStyleSheet()
        return {
            'title': ParagraphStyle('title', parent=base['Title'], textColor=colors.white,
                                    fontSize=22, leading=26, spaceAfter=4),
            'subtitle': ParagraphStyle('subtitle', parent=base['Normal'], textColor=colors.HexColor('#DDE4F0'),
                                       fontSize=10, leading=14),
            'h1': ParagraphStyle('h1', parent=base['Heading1'], textColor=NAVY, fontSize=15,
                                 leading=18, spaceBefore=14, spaceAfter=6),
            'h2': ParagraphStyle('h2', parent=base['Heading2'], textColor=NAVY, fontSize=12,
                                 leading=15, spaceBefore=10, spaceAfter=4),
            'body': ParagraphStyle('body', parent=base['Normal'], fontSize=9.5, leading=14,
                                   spaceAfter=4),
            'small': ParagraphStyle('small', parent=base['Normal'], fontSize=8, leading=11,
                                    textColor=colors.HexColor('#555555')),
        }

    @staticmethod
    def _header_table(title, subtitle):
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), NAVY),
            ('LEFTPADDING', (0, 0), (-1, -1), 14),
            ('RIGHTPADDING', (0, 0), (-1, -1), 14),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ])
        return Table([[Paragraph(title, Command._styles()['title']),
                       Paragraph(subtitle, Command._styles()['subtitle'])]],
                     colWidths=[100 * mm, 80 * mm]), style

    @staticmethod
    def _table(header_row, data_rows, widths=None):
        header_style = ParagraphStyle('th', fontSize=8.5, textColor=colors.white,
                                      fontName='Helvetica-Bold', leading=11)
        cell_style = ParagraphStyle('td', fontSize=8.5, leading=11)

        table_data = [[Paragraph(h, header_style) for h in header_row]]
        for row in data_rows:
            table_data.append([Paragraph(str(c), cell_style) for c in row])

        t = Table(table_data, colWidths=widths, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), NAVY),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT]),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#CCCCCC')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        return t

    # -- Project information PDF ----------------------------------------------
    def _build_project_pdf(self, path):
        doc = SimpleDocTemplate(
            path, pagesize=A4,
            leftMargin=18 * mm, rightMargin=18 * mm,
            topMargin=16 * mm, bottomMargin=16 * mm,
            title='Project Information', author='College Academic Resource Management System',
        )
        styles = self._styles()
        story = []

        header, hstyle = self._header_table(
            'College Academic Resource Management System',
            f'Project Information & Technical Documentation -- generated {timezone.localdate():%d %B %Y}',
        )
        header.setStyle(hstyle)
        story.append(header)

        story.append(Paragraph('1. Project Overview', styles['h1']))
        story.append(Paragraph(
            'The College Academic Resource Management System (RGCET) is a secure, role-based web '
            'platform for managing academic resources, students, subjects and staff in a '
            'multi-department college. Each department operates in a fully isolated data domain: '
            'users belonging to one department can never view, download or modify records belonging '
            'to another department. The system provides resource upload and secure download, student '
            'record management, batch Excel import/export, department-level reports, an audit trail, '
            'and a JWT-protected REST API. Deployed on Vercel as a serverless Django application '
            'with Neon PostgreSQL for production and Google Cloud Storage for file hosting.',
            styles['body']))

        story.append(Paragraph('2. Key Features', styles['h1']))
        story.append(self._table(
            ['Feature', 'Details'],
            [
                ['New User page', 'Creates teacher accounts with name, phone, email, department, password + confirm password'],
                ['Login-page registration', 'Teacher/HOD accounts can be created from the login page -- auto-login after signup (Super Admin never allowed)'],
                ['Multi-subject teachers', 'One teacher can be assigned to many subjects at creation and in dashboards'],
                ['Teacher dashboard', 'Lists every assigned subject with live per-subject resource counts'],
                ['HOD full department view', 'HOD sees all staff, subjects, students-by-year and resources of their department'],
                ['Department isolation', 'Cross-department access is blocked (403 web / 404 API)'],
                ['Excel import/export', 'Batch student import with column mapping and filtered exports'],
                ['Reports & audit trail', 'Department/college-wide reports and full activity logging'],
                ['Vercel deployment', 'Serverless deployment with automatic scaling, Python 3.12 runtime'],
                ['REST API', 'JWT-protected API with department-scoped ViewSets for all modules'],
            ],
            widths=[55 * mm, 125 * mm],
        ))

        story.append(Paragraph('3. Technology Stack', styles['h1']))
        story.append(self._table(
            ['Layer', 'Technology', 'Purpose'],
            [
                ['Backend', 'Python 3.12 / Django 5.2', 'Core framework, ORM, admin, auth'],
                ['REST API', 'Django REST Framework 3.16', 'API endpoints for each module'],
                ['Auth / JWT', 'SimpleJWT', 'Access + refresh tokens for the API'],
                ['Database (local)', 'MySQL 8.x (PyMySQL)', 'Local development data store'],
                ['Database (prod)', 'Neon PostgreSQL (free tier)', 'Production data store via dj-database-url'],
                ['Test DB', 'SQLite (in-memory)', 'Isolated test runs'],
                ['Templates', 'Django templates + Bootstrap 5', 'Responsive UI, sidebar layout'],
                ['Excel', 'pandas / openpyxl', 'Batch student import and export'],
                ['PDF', 'reportlab', 'Documentation PDF generation'],
                ['Files', 'Pillow', 'Image handling for profiles'],
                ['Static files', 'Whitenoise + GCS', 'Compressed static serving on Vercel'],
                ['File storage', 'Google Cloud Storage (15 GB free)', 'Media file uploads in production'],
                ['Hosting', 'Vercel (serverless)', 'Auto-scaling, SSL, CDN'],
                ['Env', 'python-dotenv', 'Local configuration via .env'],
            ],
            widths=[30 * mm, 55 * mm, 95 * mm],
        ))

        story.append(Paragraph('4. Architecture & Applications', styles['h1']))
        story.append(self._table(
            ['App', 'Responsibility'],
            [
                ['config', 'Settings split into base / development / testing / vercel (production)'],
                ['api', 'Vercel serverless entry point (WSGI adapter for @vercel/python)'],
                ['accounts', 'Users, StaffProfile, roles, login, New User page, staff management, auth mixins'],
                ['departments', 'Department CRUD (Super Admin only)'],
                ['subjects', 'Subjects, academic years, regulations, teacher assignments (multi-subject)'],
                ['resources', 'Resource categories and department-scoped file uploads'],
                ['students', 'Student records, filters, Excel export'],
                ['excel_manager', 'Two-step Excel import with column mapping and validation'],
                ['dashboard', 'Role-based dashboards (multi-subject teacher view, full HOD department view)'],
                ['audit', 'Audit log of every sensitive action'],
                ['core_api', 'JWT-protected REST ViewSets with department scoping'],
            ],
            widths=[30 * mm, 150 * mm],
        ))

        story.append(Paragraph('5. Deployment Architecture', styles['h1']))
        story.append(self._table(
            ['Component', 'Details'],
            [
                ['Platform', 'Vercel serverless functions (auto-scaling, global CDN)'],
                ['Runtime', '@vercel/python, Python 3.12 (runtime.txt)'],
                ['Entry point', 'api/index.py -- exports WSGI app for Vercel auto-detection'],
                ['Build config', 'vercel.json -- builds api/index.py, routes all requests to it'],
                ['Database', 'Neon PostgreSQL (free tier, 512 MB) with SSL + connection pooling'],
                ['Static files', 'Whitenoise compressed manifest or Google Cloud Storage'],
                ['Media files', 'Google Cloud Storage (free tier, 15 GB) with public read'],
                ['Settings', 'config.settings.vercel with env-var fallbacks for all options'],
                ['Security', 'HSTS, SSL redirect, CSRF protection, secure cookies'],
            ],
            widths=[35 * mm, 145 * mm],
        ))

        story.append(Paragraph('6. Roles & Access Control', styles['h1']))
        story.append(self._table(
            ['Role', 'Scope'],
            [
                ['Super Admin', 'Full access across all departments; manages departments, staff and New User creation'],
                ['HOD', 'Own department only -- sees all staff, subjects, students and resources of the department'],
                ['Teacher', 'Own department; can be assigned multiple subjects and sees them on the dashboard'],
            ],
            widths=[35 * mm, 145 * mm],
        ))

        story.append(Paragraph('7. Security Model', styles['h1']))
        story.append(Paragraph(
            'Isolation is enforced at every layer, not just hidden in the UI:', styles['body']))
        story.append(self._table(
            ['Mechanism', 'Description'],
            [
                ['DepartmentAccessMixin', 'Denies object access across departments (403 on web)'],
                ['TeacherSubjectAccessMixin', 'Teachers blocked from subjects they are not assigned to'],
                ['Role mixins', 'RoleRequired / HODOrAbove / SuperAdminRequired gate views'],
                ['API scoping', 'REST ViewSets filter by department; cross-dept returns 404'],
                ['Secure downloads', 'Files never served via /media/ -- always through an authorized view'],
                ['Audit trail', 'Uploads, downloads, imports and logins recorded with IP + user'],
                ['Deactivation', 'Deactivated accounts cannot log in or access any page'],
                ['JWT auth', '60-minute access tokens, 7-day refresh with rotation + blacklist'],
                ['Env secrets', 'SECRET_KEY, DATABASE_URL and GCS credentials via Vercel env vars'],
            ],
            widths=[50 * mm, 130 * mm],
        ))

        story.append(Paragraph('8. Key URLs', styles['h1']))
        story.append(self._table(
            ['URL', 'Purpose'],
            [
                ['/', 'Redirect to dashboard'],
                ['/accounts/', 'Login, profile, staff management'],
                ['/dashboard/', 'Role dashboards + reports'],
                ['/departments/', 'Department CRUD (Super Admin)'],
                ['/subjects/', 'Subject CRUD + teacher assignments'],
                ['/resources/', 'Resource upload / browse / download'],
                ['/students/', 'Student records + Excel export'],
                ['/excel/', 'Batch Excel import'],
                ['/audit/', 'Audit trail'],
                ['/api/v1/', 'REST API (JWT)'],
                ['/admin/', 'Django admin'],
            ],
            widths=[40 * mm, 140 * mm],
        ))

        story.append(Paragraph('9. Running the Project', styles['h1']))
        story.append(Paragraph(
            '<b>Local setup:</b> create MySQL database <i>college_management</i>, copy <i>.env.example</i> to '
            '<i>.env</i> and configure credentials, then run '
            '<i>pip install -r requirements.txt</i>, <i>python manage.py migrate</i>, '
            '<i>python manage.py seed_demo_data</i> and <i>python manage.py runserver</i>.',
            styles['body']))
        story.append(Paragraph(
            '<b>Vercel deployment:</b> push to GitHub, link to Vercel, set env vars '
            '(SECRET_KEY, DATABASE_URL, CSRF_TRUSTED_ORIGINS) in the Vercel dashboard. '
            'The app auto-deploys on every push to main.',
            styles['body']))
        story.append(Paragraph(
            '<b>Testing:</b> <i>python manage.py test --settings=config.settings.testing</i> '
            '(36 tests, SQLite in-memory).', styles['body']))
        story.append(Paragraph(
            '<b>Docs:</b> see README.md and USER_CREDENTIALS.pdf for the seeded login accounts.',
            styles['body']))

        doc.build(story)

    # -- Running commands PDF -------------------------------------------------
    def _build_commands_pdf(self, path):
        doc = SimpleDocTemplate(
            path, pagesize=A4,
            leftMargin=18 * mm, rightMargin=18 * mm,
            topMargin=16 * mm, bottomMargin=16 * mm,
            title='Running Commands', author='College Academic Resource Management System',
        )
        styles = self._styles()
        story = []

        header, hstyle = self._header_table(
            'Running Commands Guide',
            f'All commands needed to set up, run and deploy the system -- '
            f'generated {timezone.localdate():%d %B %Y}',
        )
        header.setStyle(hstyle)
        story.append(header)

        story.append(Paragraph('1. One-Click Start', styles['h1']))
        story.append(Paragraph(
            'Double-click <b>run.bat</b> in the project folder, or run it from the command line. '
            'It activates the virtual environment, installs dependencies on first run, applies '
            'pending migrations and starts the server on http://127.0.0.1:8000.', styles['body']))

        story.append(Paragraph('2. First-Time Setup', styles['h1']))
        story.append(self._table(
            ['Step', 'Command', 'What it does'],
            [
                ['Virtual env', 'python -m venv venv', 'Create an isolated environment'],
                ['Activate', 'venv\\Scripts\\activate', 'Switch into the environment (Windows)'],
                ['Install', 'pip install -r requirements.txt', 'Install all dependencies'],
                ['Env config', 'copy .env.example .env', 'Create your config file'],
                ['Database', 'python manage.py migrate', 'Create all database tables'],
                ['Seed data', 'python manage.py seed_demo_data', 'Create departments, users, subjects, students'],
                ['Start', 'python manage.py runserver', 'Start the dev server on http://127.0.0.1:8000'],
            ],
            widths=[25 * mm, 75 * mm, 80 * mm],
        ))

        story.append(Paragraph('3. Vercel Deployment', styles['h1']))
        story.append(self._table(
            ['Step', 'Command / Action', 'What it does'],
            [
                ['Push to GitHub', 'git push origin main', 'Trigger automatic Vercel deployment'],
                ['Link project', 'vercel link', 'Connect local CLI to Vercel project'],
                ['Set env vars', 'Vercel Dashboard > Settings > Env Vars', 'Configure SECRET_KEY, DATABASE_URL, etc.'],
                ['View logs', 'vercel logs', 'Check serverless function logs'],
                ['Deploy preview', 'vercel --yes', 'Deploy a preview (non-production) build'],
            ],
            widths=[30 * mm, 65 * mm, 85 * mm],
        ))

        story.append(Paragraph('4. Vercel Environment Variables', styles['h1']))
        story.append(self._table(
            ['Variable', 'Required', 'Description'],
            [
                ['SECRET_KEY', 'Yes', 'Django secret key for cryptographic signing'],
                ['DATABASE_URL', 'Yes', 'Neon PostgreSQL connection string (postgresql://...)'],
                ['CSRF_TRUSTED_ORIGINS', 'Yes', 'Comma-separated list of allowed origins (https://your-app.vercel.app)'],
                ['ALLOWED_HOSTS', 'Optional', 'Comma-separated hostnames (defaults to all)'],
                ['GS_BUCKET_NAME', 'Optional', 'Google Cloud Storage bucket for media files'],
                ['EMAIL_HOST_USER', 'Optional', 'Gmail address for sending emails'],
                ['EMAIL_HOST_PASSWORD', 'Optional', 'Gmail app password for SMTP'],
            ],
            widths=[45 * mm, 20 * mm, 115 * mm],
        ))

        story.append(Paragraph('5. Common Management Commands', styles['h1']))
        story.append(self._table(
            ['Task', 'Command'],
            [
                ['Run all tests', 'python manage.py test --settings=config.settings.testing'],
                ['Run tests for one app', 'python manage.py test accounts --settings=config.settings.testing'],
                ['Check project health', 'python manage.py check'],
                ['Make migrations', 'python manage.py makemigrations'],
                ['Apply migrations', 'python manage.py migrate'],
                ['Create a staff user', 'python manage.py seed_demo_data --password YourPass123'],
                ['Create superuser', 'python manage.py createsuperuser'],
                ['Generate PDFs', 'python manage.py generate_pdfs'],
                ['Collect static files', 'python manage.py collectstatic'],
            ],
            widths=[55 * mm, 125 * mm],
        ))

        story.append(Paragraph('6. Server Options', styles['h1']))
        story.append(self._table(
            ['Command', 'Effect'],
            [
                ['python manage.py runserver', 'Default server on http://127.0.0.1:8000'],
                ['python manage.py runserver 0.0.0.0:8000', 'Listen on all interfaces (LAN access)'],
                ['python manage.py runserver --noreload', 'Run without auto-restart on code changes'],
                ['python manage.py runserver 8080', 'Use a different port'],
            ],
            widths=[80 * mm, 100 * mm],
        ))

        story.append(Paragraph('7. Logins After Seeding', styles['h1']))
        story.append(Paragraph(
            'All seeded accounts use the password <b>RGCET@2026</b>. '
            'Log in at http://127.0.0.1:8000/accounts/login/ with <b>admin</b> '
            '(Super Admin) or a HOD/teacher account such as <b>hod_cse</b>. '
            'See USER_CREDENTIALS.pdf for the full list.', styles['body']))

        story.append(Paragraph('8. Project Files', styles['h1']))
        story.append(self._table(
            ['File', 'Purpose'],
            [
                ['manage.py', 'Django management entry point'],
                ['api/index.py', 'Vercel serverless function entry point (WSGI app)'],
                ['vercel.json', 'Vercel deployment configuration (builds, routes, env)'],
                ['runtime.txt', 'Python version for Vercel (3.12)'],
                ['requirements.txt', 'Python dependencies'],
                ['.env', 'Local environment variables (not committed to git)'],
                ['.env.example', 'Template for .env'],
                ['.vercelignore', 'Files to exclude from Vercel deployment'],
                ['run.bat', 'One-click dev server launcher (Windows)'],
                ['config/settings/base.py', 'Shared Django settings (DB, apps, JWT, middleware)'],
                ['config/settings/vercel.py', 'Production settings (Neon DB, GCS, security)'],
            ],
            widths=[50 * mm, 130 * mm],
        ))

        doc.build(story)

    # -- User credentials PDF -------------------------------------------------
    def _build_users_pdf(self, path):
        doc = SimpleDocTemplate(
            path, pagesize=A4,
            leftMargin=18 * mm, rightMargin=18 * mm,
            topMargin=16 * mm, bottomMargin=16 * mm,
            title='User Credentials', author='College Academic Resource Management System',
        )
        styles = self._styles()
        story = []

        header, hstyle = self._header_table(
            'User Accounts & Credentials',
            f'Seeded users for the College Academic Resource Management System -- '
            f'generated {timezone.localdate():%d %B %Y}',
        )
        header.setStyle(hstyle)
        story.append(header)

        profiles = StaffProfile.objects.select_related('user', 'department').order_by('role', 'user__username')
        if not profiles.exists():
            story.append(Paragraph(
                'No staff accounts exist yet. Run <b>python manage.py seed_demo_data</b> to create them.',
                styles['body']))
            doc.build(story)
            return

        rows = []
        for profile in profiles:
            rows.append([
                profile.user.username,
                profile.user.get_full_name() or profile.user.username,
                profile.get_role_display(),
                profile.department.code if profile.department else 'All',
                profile.employee_id,
                'Active' if profile.is_active else 'Inactive',
            ])

        story.append(Spacer(1, 8))
        story.append(self._table(
            ['Username', 'Name', 'Role', 'Department', 'Employee ID', 'Status'],
            rows,
            widths=[28 * mm, 42 * mm, 28 * mm, 25 * mm, 28 * mm, 19 * mm],
        ))

        story.append(Spacer(1, 10))
        story.append(Paragraph('Default Password', styles['h1']))
        story.append(Paragraph(
            f'All seeded accounts were created with the shared default password '
            f'<b>{DEFAULT_PASSWORD}</b>.', styles['body']))
        story.append(Paragraph(
            'Passwords are stored as hashes and cannot be recovered in plain text. Users can change '
            'their own password after login, and the Super Admin can reset any account via the '
            'Staff Management screens.', styles['body']))

        doc.build(story)
