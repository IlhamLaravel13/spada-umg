from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Assignment, AssignmentSubmission
from .serializers import (
    AssignmentSerializer, AssignmentSubmissionSerializer,
    AssignmentSubmissionCreateSerializer,
)


class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.select_related('class_meta', 'created_by').all()
    serializer_class = AssignmentSerializer
    search_fields = ['title', 'description']
    filterset_fields = ['class_meta', 'is_published']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class SubmissionViewSet(viewsets.ModelViewSet):
    queryset = AssignmentSubmission.objects.select_related('assignment', 'student', 'graded_by').all()
    serializer_class = AssignmentSubmissionSerializer
    filterset_fields = ['assignment', 'student', 'status']

    def get_serializer_class(self):
        if self.action == 'create':
            return AssignmentSubmissionCreateSerializer
        return AssignmentSubmissionSerializer
