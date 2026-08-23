from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'department', 'action', 'object_type', 'ip_address']
    list_filter = ['action', 'department']
    search_fields = ['user__username', 'description', 'ip_address']
    readonly_fields = [f.name for f in AuditLog._meta.get_fields()]
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        return False  # Audit logs are append-only

    def has_change_permission(self, request, obj=None):
        return False  # Cannot edit audit logs
