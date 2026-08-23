from rest_framework import serializers
from django.contrib.auth.models import User
from departments.models import Department
from accounts.models import StaffProfile
from subjects.models import Subject, AcademicYear, TeacherSubject, Regulation
from resources.models import Resource, ResourceCategory
from students.models import Student
from audit.models import AuditLog


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'code', 'name', 'status']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class StaffProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = StaffProfile
        fields = ['id', 'user', 'employee_id', 'department', 'role', 'role_display', 'phone', 'profile_photo', 'status']


class RegulationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Regulation
        fields = ['id', 'code', 'name']


class SubjectSerializer(serializers.ModelSerializer):
    department_code = serializers.CharField(source='department.code', read_only=True)
    academic_year_name = serializers.CharField(source='academic_year.name', read_only=True)
    regulation_code = serializers.CharField(source='regulation.code', read_only=True)

    class Meta:
        model = Subject
        fields = ['id', 'code', 'name', 'department', 'department_code', 'academic_year', 'academic_year_name', 'regulation_code', 'semester', 'credits', 'status']


class ResourceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceCategory
        fields = ['id', 'name', 'slug', 'description', 'icon']


class ResourceSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    subject_code = serializers.CharField(source='subject.code', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.user.get_full_name', read_only=True)
    file_size_display = serializers.CharField(read_only=True)

    class Meta:
        model = Resource
        fields = [
            'id', 'title', 'description', 'department', 'subject', 'subject_code', 'subject_name',
            'category', 'category_name', 'academic_year', 'semester', 'unit',
            'file', 'file_name', 'file_size', 'file_size_display', 'file_type', 'uploaded_by_name', 'created_at'
        ]
        read_only_fields = ['file_name', 'file_size', 'file_type', 'uploaded_by']


class StudentSerializer(serializers.ModelSerializer):
    department_code = serializers.CharField(source='department.code', read_only=True)

    class Meta:
        model = Student
        fields = [
            'id', 'register_number', 'name', 'email', 'phone', 'department',
            'department_code', 'batch', 'academic_year', 'year', 'semester', 'section', 'status'
        ]
