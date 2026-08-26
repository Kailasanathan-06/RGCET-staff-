"""Root URL configuration."""
import os
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


def health_check(request):
    """Health check endpoint — verifies database connectivity."""
    status = {'django': 'ok', 'database': 'unknown'}
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        status['database'] = 'ok'
    except Exception as e:
        status['database'] = f'error: {type(e).__name__}'
    status['secret_key'] = 'set' if settings.SECRET_KEY != 'unsafe-default-key' else 'missing!'
    status['db_backend'] = settings.DATABASES['default']['ENGINE']
    return JsonResponse(status)


urlpatterns = [
    # Health check
    path('health/', health_check),

    # Django Admin
    path('admin/', admin.site.urls),

    # Web App URLs
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('departments/', include('departments.urls', namespace='departments')),
    path('subjects/', include('subjects.urls', namespace='subjects')),
    path('resources/', include('resources.urls', namespace='resources')),
    path('students/', include('students.urls', namespace='students')),
    path('excel/', include('excel_manager.urls', namespace='excel_manager')),
    path('audit/', include('audit.urls', namespace='audit')),

    # REST API
    path('api/v1/', include('core_api.urls', namespace='api')),

    # Root redirect -> dashboard
    path('', include('dashboard.urls', namespace='dashboard_root')),
]

# Error handlers
handler400 = 'accounts.views.error_400'
handler403 = 'accounts.views.error_403'
handler404 = 'accounts.views.error_404'
handler500 = 'config.views.error_500'
