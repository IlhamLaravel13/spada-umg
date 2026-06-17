from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from accounts.models import User
from academics.models import Faculty, StudyProgram, Course, Class, Enrollment, Semester
from assignments.models import Assignment, AssignmentSubmission
from quizzes.models import Quiz, QuizAttempt
from attendance.models import Attendance, AttendanceSession
from .models import AnalyticsCache, UserActivity


class DashboardStatsView(APIView):
    def get(self, request):
        now = timezone.now()
        total_users = User.objects.count()
        total_students = User.objects.filter(role='mahasiswa').count()
        total_lecturers = User.objects.filter(role='dosen').count()
        total_faculties = Faculty.objects.filter(is_active=True).count()
        total_programs = StudyProgram.objects.filter(is_active=True).count()
        total_courses = Course.objects.filter(is_active=True).count()
        total_classes = Class.objects.filter(is_active=True).count()
        total_enrollments = Enrollment.objects.filter(status='active').count()

        active_semester = Semester.objects.filter(is_active=True).first()
        active_class_count = 0
        if active_semester:
            active_class_count = Class.objects.filter(semester=active_semester).count()

        recent_activities = UserActivity.objects.select_related('user')[:20]

        return Response({
            'overview': {
                'total_users': total_users,
                'total_students': total_students,
                'total_lecturers': total_lecturers,
                'total_faculties': total_faculties,
                'total_programs': total_programs,
                'total_courses': total_courses,
                'total_classes': total_classes,
                'total_enrollments': total_enrollments,
                'active_semester': str(active_semester) if active_semester else None,
                'active_class_count': active_class_count,
            },
            'recent_activities': [
                {
                    'id': a.id,
                    'user': a.user.username,
                    'action': a.action,
                    'timestamp': a.created_at.isoformat(),
                }
                for a in recent_activities
            ],
        })


class AcademicStatsView(APIView):
    def get(self, request):
        enrollments_by_program = StudyProgram.objects.filter(is_active=True).annotate(
            student_count=Count('courses__classes__enrollments',
                                filter=Q(courses__classes__enrollments__status='active'))
        ).values('name', 'student_count')

        return Response({
            'enrollments_by_program': enrollments_by_program,
        })


class UserActivityStatsView(APIView):
    def get(self, request):
        days = int(request.GET.get('days', 30))
        since = timezone.now() - timedelta(days=days)

        activities = UserActivity.objects.filter(created_at__gte=since)
        total = activities.count()
        by_action = activities.values('action').annotate(
            count=Count('id')
        ).order_by('-count')

        return Response({
            'total': total,
            'by_action': by_action,
            'period_days': days,
        })
