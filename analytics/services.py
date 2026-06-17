import logging
from django.db import models
from django.db.models import Count, Avg, Q, Sum, FloatField
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta

from .repositories import AnalyticsCacheRepository, UserActivityRepository
from accounts.models import User
from academics.models import Course, Enrollment, Class as ClassModel
from assignments.models import Assignment, AssignmentSubmission
from quizzes.models import Quiz, QuizAttempt
from attendance.models import Attendance, AttendanceSession

logger = logging.getLogger(__name__)


class AnalyticsService:
    def __init__(self):
        self.cache_repo = AnalyticsCacheRepository()
        self.activity_repo = UserActivityRepository()

    def _get_cached_or_compute(self, key: str, compute_func, ttl: int = 60):
        cached = self.cache_repo.get(key)
        if cached:
            return cached.data
        data = compute_func()
        self.cache_repo.set(key, data, ttl)
        return data

    def get_user_stats(self):
        def compute():
            total = User.objects.count()
            active = User.objects.filter(last_activity__gte=timezone.now() - timedelta(days=30)).count()
            return {
                'total': total,
                'active': active,
                'active_percentage': round(active / total * 100, 1) if total else 0,
                'by_role': dict(
                    User.objects.values('role').annotate(count=Count('id'))
                    .values_list('role', 'count')
                ),
                'new_this_month': User.objects.filter(
                    date_joined__gte=timezone.now() - timedelta(days=30)
                ).count(),
            }
        return self._get_cached_or_compute('user_stats', compute, 300)

    def get_course_stats(self):
        def compute():
            total_courses = Course.objects.count()
            total_classes = ClassModel.objects.count()
            total_enrollments = Enrollment.objects.count()
            return {
                'total_courses': total_courses,
                'total_classes': total_classes,
                'total_enrollments': total_enrollments,
                'avg_enrollment_per_class': round(total_enrollments / total_classes, 1) if total_classes else 0,
                'courses_by_program': dict(
                    Course.objects.values('study_program__name')
                    .annotate(count=Count('id'))
                    .values_list('study_program__name', 'count')
                ),
            }
        return self._get_cached_or_compute('course_stats', compute, 600)

    def get_attendance_rate(self, class_obj=None):
        def compute_all():
            sessions = AttendanceSession.objects.all()
            total_sessions = sessions.count()
            total_attendance = Attendance.objects.count()
            present = Attendance.objects.filter(status='present').count()
            rate = round(present / total_attendance * 100, 1) if total_attendance else 0
            return {
                'total_sessions': total_sessions,
                'total_attendance': total_attendance,
                'present': present,
                'absent': Attendance.objects.filter(status='absent').count(),
                'sick': Attendance.objects.filter(status='sick').count(),
                'permit': Attendance.objects.filter(status='permit').count(),
                'attendance_rate': rate,
            }
        if class_obj:
            def compute_class():
                sessions = AttendanceSession.objects.filter(cls=class_obj)
                total_sessions = sessions.count()
                total_attendance = Attendance.objects.filter(session__in=sessions).count()
                present = Attendance.objects.filter(session__in=sessions, status='present').count()
                rate = round(present / total_attendance * 100, 1) if total_attendance else 0
                return {
                    'total_sessions': total_sessions,
                    'total_attendance': total_attendance,
                    'present': present,
                    'absent': Attendance.objects.filter(session__in=sessions, status='absent').count(),
                    'sick': Attendance.objects.filter(session__in=sessions, status='sick').count(),
                    'permit': Attendance.objects.filter(session__in=sessions, status='permit').count(),
                    'attendance_rate': rate,
                }
            return self._get_cached_or_compute(f'attendance_rate_class_{class_obj.id}', compute_class, 300)
        return self._get_cached_or_compute('attendance_rate', compute_all, 300)

    def get_submission_rate(self, class_obj=None):
        def compute_all():
            total = AssignmentSubmission.objects.count()
            graded = AssignmentSubmission.objects.filter(score__isnull=False).count()
            on_time = AssignmentSubmission.objects.filter(submitted_at__lte=models.F('assignment__due_date')).count()
            return {
                'total_submissions': total,
                'graded': graded,
                'ungraded': total - graded,
                'on_time': on_time,
                'late': total - on_time,
                'submission_rate': round(on_time / total * 100, 1) if total else 0,
                'grading_rate': round(graded / total * 100, 1) if total else 0,
            }
        if class_obj:
            def compute_class():
                total = AssignmentSubmission.objects.filter(assignment__class_meta=class_obj).count()
                graded = AssignmentSubmission.objects.filter(assignment__class_meta=class_obj, score__isnull=False).count()
                return {
                    'total_submissions': total,
                    'graded': graded,
                    'ungraded': total - graded,
                    'grading_rate': round(graded / total * 100, 1) if total else 0,
                }
            return self._get_cached_or_compute(f'submission_rate_class_{class_obj.id}', compute_class, 300)
        return self._get_cached_or_compute('submission_rate', compute_all, 300)

    def get_grade_averages(self, class_obj=None):
        def compute_all():
            from assignments.models import AssignmentSubmission
            from quizzes.models import QuizAttempt
            assign_avg = AssignmentSubmission.objects.filter(score__isnull=False).aggregate(
                avg=Coalesce(Avg('score'), 0.0, output_field=FloatField())
            )['avg']
            quiz_avg = QuizAttempt.objects.filter(score__isnull=False).aggregate(
                avg=Coalesce(Avg('score'), 0.0, output_field=FloatField())
            )['avg']
            return {
                'average_assignment_grade': round(assign_avg, 1),
                'average_quiz_score': round(quiz_avg, 1),
                'overall_average': round((assign_avg + quiz_avg) / 2, 1),
            }
        return self._get_cached_or_compute('grade_averages', compute_all, 600)

    def get_mahasiswa_stats(self, user):
        enrollments = Enrollment.objects.filter(student=user).select_related('class_enrolled__course')
        stats = []
        for enrollment in enrollments:
            class_obj = enrollment.class_enrolled
            attendance_rate = self.get_attendance_rate(class_obj)
            submission_rate = self.get_submission_rate(class_obj)
            stats.append({
                'class_name': str(class_obj),
                'course_name': class_obj.course.name,
                'attendance_rate': attendance_rate.get('attendance_rate', 0),
                'submission_rate': submission_rate.get('submission_rate', 0),
                'total_sessions': attendance_rate.get('total_sessions', 0),
                'total_assignments': Assignment.objects.filter(class_meta=class_obj).count(),
                'submitted': AssignmentSubmission.objects.filter(assignment__class_meta=class_obj, student=user).count(),
                'grades': list(
                    AssignmentSubmission.objects.filter(
                        assignment__class_meta=class_obj, student=user, score__isnull=False
                    ).values('assignment__title', 'score')
                ),
            })
        return stats

    def get_dosen_stats(self, user):
        classes = ClassModel.objects.filter(lecturer=user).select_related('course')
        stats = []
        for class_obj in classes:
            attendance_rate = self.get_attendance_rate(class_obj)
            submission_rate = self.get_submission_rate(class_obj)
            grade_avg = self.get_grade_averages(class_obj)
            student_count = Enrollment.objects.filter(class_enrolled=class_obj).count()
            stats.append({
                'class_name': str(class_obj),
                'course_name': class_obj.course.name,
                'code': class_obj.code,
                'student_count': student_count,
                'attendance_rate': attendance_rate.get('attendance_rate', 0),
                'submission_rate': submission_rate.get('grading_rate', 0),
                'grade_average': grade_avg.get('overall_average', 0),
                'total_sessions': attendance_rate.get('total_sessions', 0),
            })
        return stats

    def get_daily_activity(self, days: int = 30):
        return self.activity_repo.get_daily_activity(days)

    def get_active_users_count(self, days: int = 7):
        return self.activity_repo.get_active_users_count(days)

    def log_activity(self, user, action: str, metadata: dict = None, ip_address: str = None):
        return self.activity_repo.log(user, action, metadata, ip_address)

    def get_total_users(self):
        return User.objects.count()

    def get_total_dosen(self):
        return User.objects.filter(role='dosen').count()

    def get_total_mahasiswa(self):
        return User.objects.filter(role='mahasiswa').count()

    def get_total_courses(self):
        return Course.objects.count()

    def get_total_classes(self):
        return ClassModel.objects.count()

    def get_recent_users(self, limit=10):
        return User.objects.order_by('-date_joined')[:limit]

    def get_recent_activities(self, limit=15):
        return self.activity_repo.get_recent(limit)

    def get_user_stats_by_role(self):
        return dict(
            User.objects.values('role').annotate(count=models.Count('id'))
            .values_list('role', 'count')
        )

    def get_enrollment_stats(self):
        total = Enrollment.objects.count()
        active = Enrollment.objects.filter(status='active').count()
        return {
            'total': total,
            'active': active,
            'completed': Enrollment.objects.filter(status='completed').count(),
            'dropped': Enrollment.objects.filter(status='dropped').count(),
        }

    def get_lecturer_total_students(self, user):
        return Enrollment.objects.filter(
            class_enrolled__lecturer=user,
            status='active'
        ).values('student').distinct().count()

    def get_lecturer_recent_attendance(self, user, limit=10):
        return AttendanceSession.objects.filter(
            class_meta__lecturer=user
        ).select_related('class_meta__course').order_by('-date', '-start_time')[:limit]

    def get_lecturer_attendance_rate(self, user):
        sessions = AttendanceSession.objects.filter(class_meta__lecturer=user)
        total_sessions = sessions.count()
        if total_sessions == 0:
            return 0
        total_attendance = Attendance.objects.filter(session__in=sessions).count()
        if total_attendance == 0:
            return 0
        present = Attendance.objects.filter(session__in=sessions, status='present').count()
        return round(present / total_attendance * 100, 1)

    def get_student_upcoming_quizzes(self, user, limit=5):
        return Quiz.objects.filter(
            class_meta__enrollments__student=user,
            is_published=True,
            start_date__gte=timezone.now()
        ).select_related('class_meta__course').distinct().order_by('start_date')[:limit]

    def get_student_recent_grades(self, user, limit=5):
        return AssignmentSubmission.objects.filter(
            student=user,
            score__isnull=False
        ).select_related('assignment__class_meta__course').order_by('-graded_at')[:limit]

    def get_student_attendance_rate(self, user):
        enrollments = Enrollment.objects.filter(student=user, status='active')
        class_ids = enrollments.values_list('class_enrolled_id', flat=True)
        sessions = AttendanceSession.objects.filter(class_meta_id__in=class_ids)
        total_sessions = sessions.count()
        if total_sessions == 0:
            return 0
        user_attendance = Attendance.objects.filter(
            session__in=sessions,
            student=user
        )
        if user_attendance.count() == 0:
            return 0
        present = user_attendance.filter(status='present').count()
        total = user_attendance.count()
        return round(present / total * 100, 1)

    def get_student_overall_grade(self, user):
        enrollments = Enrollment.objects.filter(student=user, status='active')
        grades = [e.grade_final for e in enrollments if e.grade_final is not None]
        if not grades:
            return None
        return round(sum(grades) / len(grades), 2)

    def get_system_overview(self):
        user_stats = self.get_user_stats()
        course_stats = self.get_course_stats()
        attendance_rate = self.get_attendance_rate()
        submission_rate = self.get_submission_rate()
        grade_avg = self.get_grade_averages()
        active_users = self.get_active_users_count(7)
        daily_activity = self.get_daily_activity(14)

        return {
            'user_stats': user_stats,
            'course_stats': course_stats,
            'attendance': attendance_rate,
            'submissions': submission_rate,
            'grades': grade_avg,
            'active_users_7d': active_users,
            'daily_activity': daily_activity,
        }


