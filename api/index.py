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
application = get_wsgi_application()

# Vercel handler
def handler(request, response):
    """
    Vercel serverless function handler.
    This is a simplified handler - for full Django support,
    use the vercel-python package or adapt as needed.
    """
    return application
