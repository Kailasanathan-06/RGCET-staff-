from django.contrib import admin
from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['register_number', 'name', 'department', 'batch', 'year', 'section', 'status']
    list_filter = ['department', 'batch', 'year', 'section', 'status']
    search_fields = ['register_number', 'name', 'email']
