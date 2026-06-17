from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Report
from .services import ReportService
from .repositories import ReportRepository

User = get_user_model()


class ReportModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='admin', email='admin@umg.ac.id',
            password='admin123', role='admin'
        )
        self.report = Report.objects.create(
            title='Test Report',
            report_type='academic',
            format='pdf',
            parameters={'semester_id': 1},
            generated_by=self.user,
        )

    def test_report_creation(self):
        self.assertEqual(self.report.title, 'Test Report')
        self.assertEqual(self.report.report_type, 'academic')
        self.assertEqual(self.report.format, 'pdf')
        self.assertFalse(self.report.is_ready)

    def test_report_str(self):
        self.assertEqual(str(self.report), 'Test Report')

    def test_default_ordering(self):
        report2 = Report.objects.create(
            title='Second', report_type='grade', format='csv',
            generated_by=self.user,
        )
        qs = Report.objects.all()
        self.assertEqual(qs.first(), report2)


class ReportRepositoryTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='admin', email='admin@umg.ac.id',
            password='admin123', role='admin'
        )
        self.repo = ReportRepository()
        self.report = Report.objects.create(
            title='Repo Test', report_type='attendance', format='pdf',
            generated_by=self.user,
        )

    def test_get_by_id(self):
        r = self.repo.get_by_id(self.report.id)
        self.assertIsNotNone(r)
        self.assertEqual(r.title, 'Repo Test')

    def test_get_by_type(self):
        qs = self.repo.get_by_type('attendance')
        self.assertEqual(qs.count(), 1)

    def test_get_by_user(self):
        qs = self.repo.get_by_user(self.user.id)
        self.assertEqual(qs.count(), 1)

    def test_create_report(self):
        r = self.repo.create_report(
            title='New', report_type='grade', format='excel',
            parameters={'test': True}, generated_by=self.user,
        )
        self.assertEqual(r.title, 'New')
        self.assertEqual(r.report_type, 'grade')


class ReportServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='admin', email='admin@umg.ac.id',
            password='admin123', role='admin'
        )
        self.service = ReportService()

    def test_generate_academic_report(self):
        result = self.service.generate_report(
            report_type='academic', fmt='csv',
            title='Academic Test', parameters={},
            user=self.user,
        )
        self.assertTrue(result['success'])
        self.assertEqual(result['report'].report_type, 'academic')
        self.assertEqual(result['report'].format, 'csv')

    def test_generate_user_report(self):
        result = self.service.generate_report(
            report_type='user', fmt='csv',
            title='User Report', parameters={},
            user=self.user,
        )
        self.assertTrue(result['success'])

    def test_generate_invalid_type(self):
        result = self.service.generate_report(
            report_type='invalid', fmt='pdf',
            title='Invalid', parameters={},
            user=self.user,
        )
        self.assertFalse(result['success'])


class ReportViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='admin', email='admin@umg.ac.id',
            password='admin123', role='admin'
        )
        self.report = Report.objects.create(
            title='View Test', report_type='academic', format='pdf',
            generated_by=self.user, is_ready=True,
        )

    def test_list_view_requires_login(self):
        response = self.client.get(reverse('reports:list'))
        self.assertEqual(response.status_code, 302)

    def test_list_view_authenticated(self):
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('reports:list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reports/report_list.html')

    def test_generate_view(self):
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('reports:generate'))
        self.assertEqual(response.status_code, 200)

    def test_detail_view(self):
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('reports:detail', args=[self.report.id]))
        self.assertEqual(response.status_code, 200)


class ReportURLTest(TestCase):
    def test_list_url(self):
        self.assertEqual(reverse('reports:list'), '/reports/')

    def test_generate_url(self):
        self.assertEqual(reverse('reports:generate'), '/reports/generate/')

    def test_detail_url(self):
        self.assertEqual(reverse('reports:detail', args=[1]), '/reports/1/')
