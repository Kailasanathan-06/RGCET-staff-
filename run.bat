@echo off
REM ── College Academic Resource Management System - Dev Server ──────────────
REM Usage:  run.bat
REM Starts the Django development server on http://127.0.0.1:8000
REM ──────────────────────────────────────────────────────────────────────────
cd /d "%~dp0"

REM Activate virtual environment if present
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Install dependencies (first run only)
if not exist ".venv_ok" (
    echo Installing dependencies...
    pip install -r requirements.txt
    echo done> ".venv_ok"
)

REM Run migrations if any pending (safe on every start)
python manage.py migrate

REM Start the server
python manage.py runserver 127.0.0.1:8000
