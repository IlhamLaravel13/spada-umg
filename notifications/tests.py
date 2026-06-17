from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Notification
from .services import NotificationService

User = get_user_model()


class BaseNotificationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='mahasiswa1', password='test123', role='mahasiswa',
            first_name='Mhs', last_name='Satu', nim='2024001',
        )
        self.admin = User.objects.create_user(
            username='admin1', password='test123', role='admin',
            first_name='Admin', last_name='Satu',
        )

    def _create_notification(self, **kwargs):
        data = {
            'recipient': self.user,
            'notification_type': 'info',
            'title': 'Notif Test',
            'message': 'Ini adalah pesan notifikasi test.',
        }
        data.update(kwargs)
        return Notification.objects.create(**data)


class NotificationModelTest(BaseNotificationTest):
    def test_create_notification(self):
        n = self._create_notification()
        self.assertEqual(str(n), 'Information: Notif Test')
        self.assertFalse(n.is_read)

    def test_unread_default(self):
        n = self._create_notification()
        self.assertFalse(n.is_read)
        self.assertIsNone(n.read_at)

    def test_ordering(self):
        n1 = self._create_notification(title='A', is_important=False)
        n2 = self._create_notification(title='B', is_important=True)
        qs = Notification.objects.all()
        self.assertEqual(qs.first(), n2)

    def test_indexes(self):
        indexes = [idx.fields for idx in Notification._meta.indexes]
        self.assertIn(['recipient', '-created_at'], [list(i.fields) for i in Notification._meta.indexes])


class NotificationServiceTest(BaseNotificationTest):
    def test_create(self):
        service = NotificationService()
        result = service.create(
            recipient=self.user,
            notification_type='assignment',
            title='Tugas Baru',
            message='Ada tugas baru',
        )
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['data'].id)

    def test_mark_read(self):
        n = self._create_notification()
        service = NotificationService()
        result = service.mark_read(n.id, self.user)
        self.assertTrue(result['success'])
        self.assertTrue(result['data'].is_read)
        self.assertIsNotNone(result['data'].read_at)

    def test_mark_all_read(self):
        self._create_notification(title='N1')
        self._create_notification(title='N2')
        service = NotificationService()
        result = service.mark_all_read(self.user)
        self.assertTrue(result['success'])
        self.assertEqual(result['count'], 2)

    def test_unread_count(self):
        self._create_notification()
        self._create_notification()
        self._create_notification(is_important=True)
        service = NotificationService()
        self.assertEqual(service.get_unread_count(self.user), 3)
        service.mark_all_read(self.user)
        self.assertEqual(service.get_unread_count(self.user), 0)


class NotificationViewsTest(BaseNotificationTest):
    def test_list_requires_login(self):
        response = self.client.get(reverse('notifications:list'))
        self.assertNotEqual(response.status_code, 200)

    def test_list_authenticated(self):
        self.client.login(username='mahasiswa1', password='test123')
        self._create_notification()
        response = self.client.get(reverse('notifications:list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notifications/notification_list.html')

    def test_mark_read_view(self):
        self.client.login(username='mahasiswa1', password='test123')
        n = self._create_notification()
        response = self.client.post(reverse('notifications:mark_read', args=[n.id]))
        self.assertIn(response.status_code, [200, 302])
        n.refresh_from_db()
        self.assertTrue(n.is_read)

    def test_mark_all_read_view(self):
        self.client.login(username='mahasiswa1', password='test123')
        self._create_notification(title='N1')
        self._create_notification(title='N2')
        response = self.client.post(reverse('notifications:mark_all_read'))
        self.assertIn(response.status_code, [200, 302])
        self.assertEqual(Notification.objects.filter(recipient=self.user, is_read=False).count(), 0)

    def test_get_unread(self):
        self.client.login(username='mahasiswa1', password='test123')
        self._create_notification(title='N1')
        response = self.client.get(reverse('notifications:get_unread'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)

    def test_htmx_unread(self):
        self.client.login(username='mahasiswa1', password='test123')
        self._create_notification(title='N1')
        response = self.client.get(
            reverse('notifications:get_unread'),
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
