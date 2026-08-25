"""
Vercel serverless entry point for Django.
Uses Mangum to bridge Vercel's HTTP events to Django's WSGI application.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.vercel')

from django.core.wsgi import get_wsgi_application

app = get_wsgi_application()

from mangum import Mangum

handler = Mangum(app, lifespan="off")
