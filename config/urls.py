"""Root URL configuration."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
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

    # Root redirect → dashboard
    path('', include('dashboard.urls', namespace='dashboard_root')),
]

# Error handlers
handler400 = 'accounts.views.error_400'
handler403 = 'accounts.views.error_403'
handler404 = 'accounts.views.error_404'
handler500 = 'accounts.views.error_500'
