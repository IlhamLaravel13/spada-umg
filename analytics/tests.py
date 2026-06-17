from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta

from .models import AnalyticsCache, UserActivity
from .services import AnalyticsService
from academics.models import Faculty, StudyProgram, AcademicYear, Semester, Course, Class as ClassModel

User = get_user_model()


class BaseAnalyticsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            username='admin1', password='test123', role='admin',
            first_name='Admin', last_name='Satu',
        )
        self.dosen = User.objects.create_user(
            username='dosen1', password='test123', role='dosen',
            first_name='Dosen', last_name='Satu', nidn='12345',
        )
        self.mahasiswa = User.objects.create_user(
            username='mhs1', password='test123', role='mahasiswa',
            first_name='Mhs', last_name='Satu', nim='2024001',
        )
        faculty = Faculty.objects.create(name='FT', code='FT')
        sp = StudyProgram.objects.create(faculty=faculty, name='TI', code='TI', degree='s1')
        course = Course.objects.create(study_program=sp, code='CS101', name='Algoritma', credits=3, semester=1)
        ay = AcademicYear.objects.create(year='2024/2025', start_date='2024-09-01', end_date='2025-08-31')
        semester = Semester.objects.create(
            academic_year=ay, name='Ganjil 2024', code='G2024',
            start_date='2024-09-01', end_date='2025-01-31',
        )
        self.class_obj = ClassModel.objects.create(
            course=course, semester=semester, name='A', code='CS101-A',
            lecturer=self.dosen, max_students=40,
        )


class AnalyticsCacheModelTest(BaseAnalyticsTest):
    def test_create_cache(self):
        cache = AnalyticsCache.objects.create(
            key='test_key',
            data={'value': 42},
            expires_at=timezone.now() + timedelta(hours=1),
        )
        self.assertEqual(cache.key, 'test_key')
        self.assertEqual(cache.data['value'], 42)
        self.assertEqual(str(cache), 'test_key')

    def test_unique_key(self):
        AnalyticsCache.objects.create(key='dup', data={}, expires_at=timezone.now() + timedelta(hours=1))
        with self.assertRaises(Exception):
            AnalyticsCache.objects.create(key='dup', data={}, expires_at=timezone.now() + timedelta(hours=1))


class UserActivityModelTest(BaseAnalyticsTest):
    def test_create_activity(self):
        activity = UserActivity.objects.create(
            user=self.mahasiswa, action='login',
            metadata={'ip': '127.0.0.1'},
            ip_address='127.0.0.1',
        )
        self.assertEqual(str(activity), f'{self.mahasiswa} - login')
        self.assertEqual(activity.action, 'login')

    def test_ordering(self):
        a1 = UserActivity.objects.create(user=self.mahasiswa, action='login', created_at=timezone.now() - timedelta(hours=1))
        a2 = UserActivity.objects.create(user=self.mahasiswa, action='logout')
        qs = UserActivity.objects.all()
        self.assertEqual(qs.first(), a2)


class AnalyticsServiceTest(BaseAnalyticsTest):
    def test_user_stats(self):
        service = AnalyticsService()
        stats = service.get_user_stats()
        self.assertIn('total', stats)
        self.assertIn('by_role', stats)
        self.assertEqual(stats['total'], 3)

    def test_course_stats(self):
        service = AnalyticsService()
        stats = service.get_course_stats()
        self.assertIn('total_courses', stats)
        self.assertEqual(stats['total_courses'], 1)

    def test_attendance_rate(self):
        service = AnalyticsService()
        rate = service.get_attendance_rate()
        self.assertIn('attendance_rate', rate)

    def test_log_activity(self):
        service = AnalyticsService()
        activity = service.log_activity(self.mahasiswa, 'login', {'ip': '127.0.0.1'}, '127.0.0.1')
        self.assertEqual(activity.action, 'login')
        self.assertEqual(activity.user, self.mahasiswa)

    def test_cache_works(self):
        service = AnalyticsService()
        stats1 = service.get_user_stats()
        stats2 = service.get_user_stats()
        self.assertEqual(stats1, stats2)


class AnalyticsViewsTest(BaseAnalyticsTest):
    def test_admin_dashboard_requires_admin(self):
        self.client.login(username='mhs1', password='test123')
        response = self.client.get(reverse('analytics:admin_dashboard'))
        self.assertNotEqual(response.status_code, 200)

    def test_admin_dashboard_access(self):
        self.client.login(username='admin1', password='test123')
        response = self.client.get(reverse('analytics:admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'analytics/admin_dashboard.html')

    def test_dosen_stats_by_dosen(self):
        self.client.login(username='dosen1', password='test123')
        response = self.client.get(reverse('analytics:dosen_stats'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'analytics/dosen_stats.html')

    def test_mahasiswa_stats(self):
        self.client.login(username='mhs1', password='test123')
        response = self.client.get(reverse('analytics:mahasiswa_stats'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'analytics/mahasiswa_stats.html')

    def test_user_stats_api_forbidden(self):
        self.client.login(username='mhs1', password='test123')
        response = self.client.get(reverse('analytics:user_stats_json'))
        self.assertEqual(response.status_code, 403)

    def test_user_stats_api_admin(self):
        self.client.login(username='admin1', password='test123')
        response = self.client.get(reverse('analytics:user_stats_json'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('total', data)
