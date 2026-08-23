"""
Vercel serverless entry point for Django.
This file maps Vercel's serverless functions to Django's WSGI application.
"""
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.vercel')

# Import Django and set up
from django.core.wsgi import get_wsgi_application

app = get_wsgi_application()
application = app
