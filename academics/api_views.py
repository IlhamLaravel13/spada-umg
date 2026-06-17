from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Faculty, StudyProgram, AcademicYear, Semester, Course, Class, Enrollment
from .serializers import (
    FacultySerializer, StudyProgramSerializer, AcademicYearSerializer,
    SemesterSerializer, CourseSerializer, ClassSerializer,
    EnrollmentSerializer, EnrollmentCreateSerializer,
)


class FacultyViewSet(viewsets.ModelViewSet):
    queryset = Faculty.objects.all()
    serializer_class = FacultySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code']
    filterset_fields = ['is_active']


class StudyProgramViewSet(viewsets.ModelViewSet):
    queryset = StudyProgram.objects.select_related('faculty').all()
    serializer_class = StudyProgramSerializer
    search_fields = ['name', 'code']
    filterset_fields = ['faculty', 'is_active', 'degree']


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.select_related('study_program__faculty').all()
    serializer_class = CourseSerializer
    search_fields = ['name', 'code']
    filterset_fields = ['study_program', 'is_active', 'credits', 'semester']


class ClassViewSet(viewsets.ModelViewSet):
    queryset = Class.objects.select_related('course', 'semester', 'lecturer').all()
    serializer_class = ClassSerializer
    search_fields = ['name', 'code', 'course__name', 'course__code']
    filterset_fields = ['course', 'semester', 'is_active', 'class_type']


class SemesterViewSet(viewsets.ModelViewSet):
    queryset = Semester.objects.select_related('academic_year').all()
    serializer_class = SemesterSerializer
    filterset_fields = ['academic_year', 'is_active']


class AcademicYearViewSet(viewsets.ModelViewSet):
    queryset = AcademicYear.objects.all()
    serializer_class = AcademicYearSerializer
    search_fields = ['year']
    filterset_fields = ['is_active']


class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.select_related('student', 'class_enrolled').all()
    serializer_class = EnrollmentSerializer
    filterset_fields = ['student', 'class_enrolled', 'status']

    def get_serializer_class(self):
        if self.action == 'create':
            return EnrollmentCreateSerializer
        return EnrollmentSerializer
