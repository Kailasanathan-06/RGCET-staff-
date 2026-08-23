from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.http import FileResponse, Http404
from django.core.exceptions import PermissionDenied

from departments.models import Department
from accounts.models import StaffProfile
from subjects.models import Subject, TeacherSubject
from resources.models import Resource
from students.models import Student
from audit.models import AuditLog

from .serializers import (
    DepartmentSerializer, StaffProfileSerializer, SubjectSerializer,
    ResourceSerializer, StudentSerializer
)


class ScopedQuerySetMixin:
    """Enforces strict department-level and role-level API access boundaries."""
    
    def get_user_department(self):
        profile = self.request.user.profile
        if profile.is_super_admin:
            return None
        return profile.department

    def get_scoped_queryset(self, model_class):
        dept = self.get_user_department()
        if dept is None:
            return model_class.objects.all()
        return model_class.objects.filter(department=dept)


class DepartmentViewSet(ScopedQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        dept = self.get_user_department()
        if dept is None:
            return Department.objects.all()
        return Department.objects.filter(id=dept.id)


class SubjectViewSet(ScopedQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = self.get_scoped_queryset(Subject).filter(status='active')
        profile = self.request.user.profile
        
        # Teacher: only assigned subjects
        if profile.is_teacher:
            assigned_ids = TeacherSubject.objects.filter(
                teacher=profile
            ).values_list('subject_id', flat=True)
            qs = qs.filter(id__in=assigned_ids)
            
        return qs


class StudentViewSet(ScopedQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.get_scoped_queryset(Student)

    def perform_create(self, serializer):
        profile = self.request.user.profile
        if not profile.is_super_admin:
            # Enforce HOD/Teacher's department on creation
            serializer.save(department=profile.department)
        else:
            serializer.save()


class ResourceViewSet(ScopedQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = ResourceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = self.get_scoped_queryset(Resource).filter(status='active')
        profile = self.request.user.profile

        # Teacher: filter to assigned subjects
        if profile.is_teacher:
            assigned_ids = TeacherSubject.objects.filter(
                teacher=profile
            ).values_list('subject_id', flat=True)
            qs = qs.filter(subject_id__in=assigned_ids)

        return qs

    def perform_create(self, serializer):
        profile = self.request.user.profile
        subject = serializer.validated_data['subject']
        
        # Validation: Teacher must be assigned to the subject
        if profile.is_teacher:
            is_assigned = TeacherSubject.objects.filter(
                teacher=profile,
                subject=subject
            ).exists()
            if not is_assigned:
                raise PermissionDenied("You are not assigned to this subject.")

        serializer.save(
            uploaded_by=profile,
            department=subject.department
        )

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        resource = get_object_or_404(Resource, pk=pk, status='active')
        profile = request.user.profile

        # Validate department
        if not profile.is_super_admin and resource.department != profile.department:
            raise PermissionDenied("Unauthorized department access.")

        # Validate subject assignment for teachers
        if profile.is_teacher:
            is_assigned = TeacherSubject.objects.filter(
                teacher=profile,
                subject=resource.subject
            ).exists()
            if not is_assigned:
                raise PermissionDenied("Unauthorized subject access.")

        try:
            file_handle = resource.file.open('rb')
        except FileNotFoundError:
            raise Http404("File not found.")

        response = FileResponse(file_handle)
        response['Content-Type'] = resource.file_type or 'application/octet-stream'
        response['Content-Disposition'] = f'attachment; filename="{resource.file_name}"'
        
        AuditLog.log(
            user=request.user,
            action=AuditLog.ACTION_DOWNLOAD,
            description=f"API Downloaded: {resource.title}",
            obj=resource,
            ip_address=request.client_ip
        )
        return response


class UserProfileViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def me(self, request):
        profile = get_object_or_404(StaffProfile, user=request.user)
        serializer = StaffProfileSerializer(profile)
        return Response(serializer.data)
