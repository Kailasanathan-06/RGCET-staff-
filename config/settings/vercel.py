"""
Vercel production settings.
Uses PostgreSQL (Neon free tier) + Google Cloud Storage (15GB free).
Falls back to SQLite and local filesystem when env vars are missing.
"""
from .base import *  # noqa
import os
from django.core.management.utils import get_random_secret_key
import dj_database_url

# ─── Debug & Security ────────────────────────────────────────────────────────
DEBUG = False
_base_secret = SECRET_KEY
SECRET_KEY = os.getenv('SECRET_KEY') or _base_secret or get_random_secret_key()

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('ALLOWED_HOSTS', '').split(',')
    if host.strip()
] or ['*']

# ─── Database ─────────────────────────────────────────────────────────────────
_db_url = os.getenv('DATABASE_URL', '')
if _db_url:
    DATABASES = {
        'default': dj_database_url.config(
            default=_db_url,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=_db_url.startswith('postgres'),
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ─── Static Files ────────────────────────────────────────────────────────────
STATIC_ROOT = BASE_DIR / 'staticfiles'

GS_BUCKET_NAME = os.getenv('GS_BUCKET_NAME')

if GS_BUCKET_NAME:
    STATIC_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/static/'
    STATICFILES_STORAGE = 'config.storages.GoogleCloudStaticStorage'
else:
    STATIC_URL = '/static/'
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'audit.middleware.AuditMiddleware',
]

# ─── Media Files (Google Cloud Storage if configured, local fallback) ────────
if GS_BUCKET_NAME:
    DEFAULT_FILE_STORAGE = 'config.storages.GoogleCloudMediaStorage'
    GS_PROJECT_ID = os.getenv('GS_PROJECT_ID')
    GS_DEFAULT_ACL = 'publicRead'
    GS_QUERYSTRING_AUTH = False
    GS_FILE_OVERWRITE = False
    GS_TYPE = 'service_account'
    GS_PRIVATE_KEY_ID = os.getenv('GS_PRIVATE_KEY_ID')
    GS_PRIVATE_KEY = (os.getenv('GS_PRIVATE_KEY') or '').replace('\\n', '\n')
    GS_CLIENT_EMAIL = os.getenv('GS_CLIENT_EMAIL')
    GS_CLIENT_ID = os.getenv('GS_CLIENT_ID')
    GS_AUTH_URI = 'https://accounts.google.com/o/oauth2/auth'
    GS_TOKEN_URI = 'https://oauth2.googleapis.com/token'

# ─── CSRF & Security ─────────────────────────────────────────────────────────
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',')
    if origin.strip()
]
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# ─── Email ────────────────────────────────────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# ─── File Upload Limits ──────────────────────────────────────────────────────
MAX_UPLOAD_SIZE = 50 * 1024 * 1024

# ─── Logging ─────────────────────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
