"""
Test settings — run the test suite against an in-memory SQLite database.

Useful on machines where the MySQL user has no permission to create a
test database. All models in this project are portable to SQLite.

Usage:
    python manage.py test --settings=config.settings.testing
"""
from .base import *  # noqa

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Fast, silent tests
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

# Noisy audit middleware is fine in tests (it only attaches attributes)
