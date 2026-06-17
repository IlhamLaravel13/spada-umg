from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Quiz, QuizQuestion, QuizAttempt
from .serializers import (
    QuizSerializer, QuizQuestionSerializer, QuizQuestionCreateSerializer,
    QuizAttemptSerializer, QuizResultSerializer,
)


class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.prefetch_related('questions__answers').all()
    serializer_class = QuizSerializer
    search_fields = ['title']
    filterset_fields = ['class_meta', 'is_published']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class QuizQuestionViewSet(viewsets.ModelViewSet):
    queryset = QuizQuestion.objects.prefetch_related('answers').all()
    serializer_class = QuizQuestionSerializer
    filterset_fields = ['quiz']

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return QuizQuestionCreateSerializer
        return QuizQuestionSerializer


class QuizAttemptViewSet(viewsets.ModelViewSet):
    queryset = QuizAttempt.objects.select_related('quiz', 'student').all()
    serializer_class = QuizAttemptSerializer
    filterset_fields = ['quiz', 'student']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return QuizResultSerializer
        return QuizAttemptSerializer
