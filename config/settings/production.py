"""Production settings — requires all env vars set."""
from .base import *  # noqa

DEBUG = False

# Security hardening
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Trusted origins for CSRF (update to your domain)
CSRF_TRUSTED_ORIGINS = [
    'https://yourdomain.com',
]

# Use real email in production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Static files collected with `collectstatic`
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
