from django.contrib import admin
from .models import AcademicYear, Regulation, Subject, TeacherSubject


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_year', 'end_year', 'is_current']
    list_filter = ['is_current']


@admin.register(Regulation)
class RegulationAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'status']
    list_filter = ['status']


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'department', 'semester', 'academic_year', 'status']
    list_filter = ['department', 'semester', 'status', 'academic_year']
    search_fields = ['code', 'name']


@admin.register(TeacherSubject)
class TeacherSubjectAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'subject', 'academic_year', 'assigned_at']
    list_filter = ['subject__department', 'academic_year']
    raw_id_fields = ['teacher', 'subject', 'assigned_by']
