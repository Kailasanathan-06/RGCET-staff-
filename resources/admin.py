from django.contrib import admin
from .models import ResourceCategory, Resource


@admin.register(ResourceCategory)
class ResourceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'sort_order']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'department', 'subject', 'uploaded_by', 'created_at', 'status']
    list_filter = ['department', 'category', 'status', 'academic_year']
    search_fields = ['title', 'subject__name', 'subject__code']
    readonly_fields = ['file_name', 'file_size', 'file_type', 'created_at', 'updated_at']
