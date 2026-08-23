# College Academic Resource Management System

A Django-based web application for managing academic resources, students, subjects,
and staff for a multi-department college (RGCET). Every module is **strictly
department-scoped**: a CSE teacher can never read, download, or modify ECE data.

---

## Tech Stack

| Layer        | Technology                                  |
|--------------|---------------------------------------------|
| Backend      | Django 5.2, Python 3.13                      |
| API          | Django REST Framework 3.16 + JWT (SimpleJWT) |
| Database     | MySQL 8.x (production), SQLite (tests)       |
| Templates    | Django templates + Bootstrap 5 + Bootstrap Icons |
| Excel        | pandas, openpyxl                            |
| PDF          | reportlab                                  |
| Extras       | Pillow, django-filter, python-dotenv        |

---

## Project Structure

```
college_management/
├── accounts/          # Users, roles, staff management, login, mixins
├── api/               # (legacy placeholder, not installed)
├── audit/             # Audit log for every sensitive action
├── config/            # Settings split: base / development / production / testing
├── core_api/          # REST API (JWT-protected ViewSets)
├── dashboard/         # Role dashboards + reports
├── departments/       # Department CRUD (Super Admin only)
├── excel_manager/     # Batch Excel/CSV student import
├── resources/         # Resource categories + file uploads (secure download)
├── students/          # Student records + Excel export
├── subjects/          # Subjects, regulations, academic years, teacher assignments
├── static/            # CSS / JS / images
└── templates/         # Shared templates (base/base.html etc.)
```

## Roles

| Role        | Scope                                                        |
|-------------|--------------------------------------------------------------|
| Super Admin | Everything across all departments                            |
| HOD         | Own department only (subjects, students, resources, import/export) |
| Teacher     | Own department AND only subjects explicitly assigned to them  |

## Setup (Windows / MySQL)

1. **Create the virtual environment and install dependencies**

   ```bat
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Create the MySQL database**

   ```sql
   CREATE DATABASE college_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'RGCET'@'localhost' IDENTIFIED BY 'RGCET123';
   GRANT ALL PRIVILEGES ON college_management.* TO 'RGCET'@'localhost';
   FLUSH PRIVILEGES;
   ```

3. **Configure environment** — copy `.env.example` to `.env` and edit:

   ```bat
   copy .env.example .env
   ```

   ```dotenv
   DB_NAME=college_management
   DB_USER=RGCET
   DB_PASSWORD=RGCET123
   DB_HOST=127.0.0.1
   DB_PORT=3306
   ```

4. **Migrate and seed**

   ```bat
   python manage.py migrate
   python manage.py seed_demo_data          REM creates departments, users, subjects, sample students
   python manage.py runserver
   ```

   Open `http://127.0.0.1:8000` and log in as `admin` / `RGCET@2026`.

## Running Tests

Tests run on an in-memory SQLite database (the MySQL user has no permission to
create a `test_*` database):

```bat
python manage.py test --settings=config.settings.testing
```

36 tests cover: cross-department 403 isolation, API 404 scoping, Excel import
validation, export filtering, and staff account deactivation.

## Key URLs

| Path                | Purpose                              |
|---------------------|--------------------------------------|
| `/`                 | Redirect to dashboard                |
| `/accounts/`        | Login / profile / staff management   |
| `/dashboard/`       | Role dashboards + reports            |
| `/departments/`     | Department CRUD (Super Admin)        |
| `/subjects/`        | Subject CRUD + teacher assignments   |
| `/resources/`       | Resource upload / browse / download  |
| `/students/`        | Student records + Excel export       |
| `/excel/`           | Batch Excel import                   |
| `/audit/`           | Audit trail                          |
| `/api/v1/`          | REST API (JWT)                       |
| `/admin/`           | Django admin                         |

## Security Model

- `accounts/mixins.py` — `DepartmentAccessMixin`, `TeacherSubjectAccessMixin`,
  `RoleRequiredMixin`, `HODOrAboveMixin`, `SuperAdminRequiredMixin`.
- Cross-department object access returns **403 Forbidden** (web) and **404**
  (API, to avoid leaking existence).
- Files are never served from `/media/` directly — always through
  `SecureDownloadView` which enforces department + subject isolation.
- Every sensitive action is written to the `audit` log with user, IP, and
  department.
- Accounts can be deactivated by the Super Admin; deactivated users cannot log in.

## Generating PDFs

Project documentation PDFs (project information and user credentials) are
generated with reportlab:

```bat
python manage.py generate_pdfs
```

This writes `PROJECT_INFORMATION.pdf` and `USER_CREDENTIALS.pdf` to the project
root.
