"""
Vercel serverless entry point for Django.
Vercel's @vercel/python runtime natively handles WSGI apps.
Just export the WSGI app as `app`.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.vercel')

from django.core.wsgi import get_wsgi_application

app = get_wsgi_application()
