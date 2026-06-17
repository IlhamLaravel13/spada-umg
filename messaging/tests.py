from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import Conversation, Message

User = get_user_model()


class BaseMessagingTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            username='admin1', password='test123', role='admin',
            first_name='Admin', last_name='Satu',
        )
        self.dosen = User.objects.create_user(
            username='dosen1', password='test123', role='dosen',
            first_name='Dosen', last_name='Satu',
        )
        self.mahasiswa = User.objects.create_user(
            username='mhs1', password='test123', role='mahasiswa',
            first_name='Mhs', last_name='Satu', nim='2024001',
        )
        self.mahasiswa2 = User.objects.create_user(
            username='mhs2', password='test123', role='mahasiswa',
            first_name='Mhs', last_name='Dua', nim='2024002',
        )

    def _create_conversation(self, participants=None, **kwargs):
        data = {'subject': 'Test Chat', 'is_group': False}
        data.update(kwargs)
        conv = Conversation.objects.create(**data)
        if participants:
            for user in participants:
                conv.participants.add(user)
        return conv

    def _create_message(self, conversation, sender, **kwargs):
        data = {'conversation': conversation, 'sender': sender, 'body': 'Test message'}
        data.update(kwargs)
        return Message.objects.create(**data)


class ConversationModelTest(BaseMessagingTest):
    def test_create_conversation(self):
        conv = self._create_conversation(subject='Diskusi', participants=[self.dosen, self.mahasiswa])
        self.assertEqual(conv.subject, 'Diskusi')
        self.assertFalse(conv.is_group)
        self.assertIn(self.dosen, conv.participants.all())

    def test_conversation_ordering(self):
        c1 = self._create_conversation(participants=[self.dosen, self.mahasiswa])
        c2 = self._create_conversation(participants=[self.dosen, self.mahasiswa2])
        qs = Conversation.objects.all()
        self.assertEqual(qs.first(), c2)


class MessageModelTest(BaseMessagingTest):
    def test_create_message(self):
        conv = self._create_conversation(participants=[self.dosen, self.mahasiswa])
        msg = self._create_message(conversation=conv, sender=self.dosen)
        self.assertEqual(msg.body, 'Test message')
        self.assertFalse(msg.is_read)
        self.assertIsNone(msg.read_at)

    def test_message_ordering(self):
        conv = self._create_conversation(participants=[self.dosen, self.mahasiswa])
        m1 = self._create_message(conversation=conv, sender=self.dosen, body='First')
        m2 = self._create_message(conversation=conv, sender=self.mahasiswa, body='Second')
        qs = Message.objects.filter(conversation=conv)
        self.assertEqual(qs.first(), m1)
        self.assertEqual(qs.last(), m2)

    def test_mark_as_read(self):
        conv = self._create_conversation(participants=[self.dosen, self.mahasiswa])
        msg = self._create_message(conversation=conv, sender=self.dosen)
        self.assertFalse(msg.is_read)
        msg.is_read = True
        from django.utils import timezone
        msg.read_at = timezone.now()
        msg.save()
        msg.refresh_from_db()
        self.assertTrue(msg.is_read)
        self.assertIsNotNone(msg.read_at)


class MessagingViewsTest(BaseMessagingTest):
    def test_inbox_requires_login(self):
        response = self.client.get(reverse('messaging:inbox'))
        self.assertNotEqual(response.status_code, 200)

    def test_inbox_authenticated(self):
        self.client.login(username='mhs1', password='test123')
        response = self.client.get(reverse('messaging:inbox'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'messaging/inbox.html')

    def test_conversation_detail(self):
        self.client.login(username='mhs1', password='test123')
        conv = self._create_conversation(participants=[self.dosen, self.mahasiswa])
        response = self.client.get(reverse('messaging:conversation_detail', args=[conv.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'messaging/conversation_detail.html')

    def test_start_conversation_get(self):
        self.client.login(username='mhs1', password='test123')
        response = self.client.get(reverse('messaging:start_conversation'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'messaging/new_message.html')

    def test_start_conversation_post(self):
        self.client.login(username='mhs1', password='test123')
        response = self.client.post(reverse('messaging:start_conversation'), {
            'recipient': self.dosen.id,
        })
        self.assertIn(response.status_code, [200, 302])
        self.assertTrue(Conversation.objects.filter(participants=self.mahasiswa).exists())

    def test_send_message(self):
        self.client.login(username='mhs1', password='test123')
        conv = self._create_conversation(participants=[self.dosen, self.mahasiswa])
        response = self.client.post(reverse('messaging:send_message', args=[conv.id]), {
            'body': 'Hello!',
        })
        self.assertIn(response.status_code, [200, 302])
        self.assertTrue(Message.objects.filter(body='Hello!').exists())

    def test_unread_count(self):
        self.client.login(username='dosen1', password='test123')
        response = self.client.get(reverse('messaging:unread_count'))
        self.assertEqual(response.status_code, 200)

    def test_mark_as_read(self):
        self.client.login(username='mhs1', password='test123')
        conv = self._create_conversation(participants=[self.dosen, self.mahasiswa])
        msg = self._create_message(conversation=conv, sender=self.dosen)
        response = self.client.post(reverse('messaging:mark_read', args=[msg.id]))
        self.assertIn(response.status_code, [200, 302])
        msg.refresh_from_db()
        self.assertTrue(msg.is_read)


class MessagingServiceTest(BaseMessagingTest):
    def test_conversation_service_create(self):
        from .services import ConversationService
        service = ConversationService()
        result = service.create(
            participants=[self.dosen, self.mahasiswa],
            subject='Service Test',
        )
        self.assertTrue(result['success'])
        self.assertIsNotNone(service.get_by_id(result['data'].id))

    def test_conversation_service_get_or_create_direct(self):
        from .services import ConversationService
        service = ConversationService()
        result = service.get_or_create_direct(self.mahasiswa, self.dosen.id)
        self.assertTrue(result['success'])

    def test_message_service_send(self):
        from .services import MessageService
        service = MessageService()
        conv = self._create_conversation(participants=[self.dosen, self.mahasiswa])
        result = service.send(conv.id, self.mahasiswa, 'Service message')
        self.assertTrue(result['success'])

    def test_message_service_mark_read(self):
        from .services import MessageService
        service = MessageService()
        conv = self._create_conversation(participants=[self.dosen, self.mahasiswa])
        msg = self._create_message(conversation=conv, sender=self.dosen)
        result = service.mark_as_read(msg.id)
        self.assertTrue(result['success'])

    def test_unread_service(self):
        from .services import UnreadService
        service = UnreadService()
        count = service.get_unread_count(self.mahasiswa)
        self.assertEqual(count, 0)
        conv = self._create_conversation(participants=[self.dosen, self.mahasiswa])
        self._create_message(conversation=conv, sender=self.dosen)
        count = service.get_unread_count(self.mahasiswa)
        self.assertEqual(count, 1)

    def test_unread_by_conversation(self):
        from .services import UnreadService
        service = UnreadService()
        conv = self._create_conversation(participants=[self.dosen, self.mahasiswa])
        self._create_message(conversation=conv, sender=self.dosen, body='Unread msg')
        result = service.get_unread_by_conversation(self.mahasiswa)
        self.assertIn(conv.id, result)
        self.assertEqual(result[conv.id], 1)
