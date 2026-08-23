"""
Vercel production settings.
Uses PostgreSQL (Neon free tier) + Google Cloud Storage (15GB free).
"""
from .base import *  # noqa
import os
import dj_database_url

# ─── Debug & Security ────────────────────────────────────────────────────────
DEBUG = False
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required")

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('ALLOWED_HOSTS', '').split(',')
    if host.strip()
]

# ─── Database ─────────────────────────────────────────────────────────────────
# Free tier: 512MB storage, 24/7 compute
_db_url = os.getenv('DATABASE_URL', '')
DATABASES = {
    'default': dj_database_url.config(
        default=_db_url,
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=_db_url.startswith('postgres'),
    )
}

# ─── Static Files (Google Cloud Storage) ─────────────────────────────────────
STATIC_URL = f'https://storage.googleapis.com/{os.getenv("GS_BUCKET_NAME")}/static/'
STATICFILES_STORAGE = 'config.storages.GoogleCloudStaticStorage'

# ─── Media Files (Google Cloud Storage) ──────────────────────────────────────
# Free tier: 15GB storage (same as Gmail account!)
DEFAULT_FILE_STORAGE = 'config.storages.GoogleCloudMediaStorage'
GS_BUCKET_NAME = os.getenv('GS_BUCKET_NAME')
GS_PROJECT_ID = os.getenv('GS_PROJECT_ID')
GS_DEFAULT_ACL = 'publicRead'
GS_QUERYSTRING_AUTH = False
GS_FILE_OVERWRITE = False

# Google Cloud credentials (from service account JSON)
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

# ─── Email (Gmail SMTP) ─────────────────────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# ─── File Upload Limits ──────────────────────────────────────────────────────
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB

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
