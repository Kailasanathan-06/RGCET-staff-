from django.contrib import admin
from .models import Department

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['code', 'name']
    ordering = ['code']
