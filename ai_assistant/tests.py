from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import AIProvider, AIConversation, AIMessage
from .services import AIService, OpenAIService, GeminiService
from .repositories import AIProviderRepository, AIConversationRepository, AIMessageRepository

User = get_user_model()


class BaseAITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', email='test@umg.ac.id',
            password='test1234', role='mahasiswa', nim='2024001',
        )
        self.admin = User.objects.create_user(
            username='admin', email='admin@umg.ac.id',
            password='test1234', role='admin', is_staff=True,
        )


class AIModelTest(BaseAITest):
    def setUp(self):
        super().setUp()
        self.provider = AIProvider.objects.create(
            name='openai', api_key='sk-test1234567890', is_active=True, model='gpt-4'
        )
        self.conversation = AIConversation.objects.create(
            user=self.user, title='Test Chat'
        )

    def test_provider_creation(self):
        self.assertEqual(self.provider.name, 'openai')
        self.assertTrue(self.provider.is_active)
        self.assertIn('OpenAI', str(self.provider))

    def test_conversation_creation(self):
        self.assertEqual(self.conversation.title, 'Test Chat')
        self.assertEqual(self.conversation.user, self.user)
        self.assertEqual(str(self.conversation), 'Test Chat')

    def test_message_creation(self):
        msg = AIMessage.objects.create(
            conversation=self.conversation, role='user', content='Halo'
        )
        self.assertEqual(msg.role, 'user')
        self.assertEqual(msg.content, 'Halo')
        self.assertIn('User', str(msg))

    def test_conversation_ordering(self):
        c2 = AIConversation.objects.create(user=self.user, title='Second')
        qs = AIConversation.objects.all()
        self.assertEqual(qs.first(), c2)

    def test_message_ordering(self):
        m1 = AIMessage.objects.create(conversation=self.conversation, role='user', content='A')
        m2 = AIMessage.objects.create(conversation=self.conversation, role='assistant', content='B')
        qs = AIMessage.objects.filter(conversation=self.conversation)
        self.assertEqual(list(qs), [m1, m2])


class AIRepositoryTest(BaseAITest):
    def setUp(self):
        super().setUp()
        self.provider_repo = AIProviderRepository()
        self.conv_repo = AIConversationRepository()
        self.msg_repo = AIMessageRepository()
        self.provider = AIProvider.objects.create(
            name='openai', api_key='sk-test', is_active=True
        )
        self.conversation = AIConversation.objects.create(user=self.user, title='Test')

    def test_get_active_provider(self):
        p = self.provider_repo.get_active()
        self.assertIsNotNone(p)
        self.assertEqual(p.name, 'openai')

    def test_get_provider_by_name(self):
        p = self.provider_repo.get_by_name('openai')
        self.assertIsNotNone(p)

    def test_create_conversation(self):
        conv = self.conv_repo.create(self.user.id, 'New Chat')
        self.assertEqual(conv.title, 'New Chat')

    def test_get_conversation_by_user(self):
        qs = self.conv_repo.get_by_user(self.user.id)
        self.assertEqual(qs.count(), 1)

    def test_create_message(self):
        msg = self.msg_repo.create(self.conversation.id, 'user', 'Hello')
        self.assertEqual(msg.content, 'Hello')
        self.assertEqual(msg.role, 'user')

    def test_get_messages(self):
        self.msg_repo.create(self.conversation.id, 'user', 'M1')
        self.msg_repo.create(self.conversation.id, 'assistant', 'M2')
        qs = self.msg_repo.get_by_conversation(self.conversation.id)
        self.assertEqual(qs.count(), 2)

    def test_delete_conversation(self):
        self.conv_repo.delete(self.conversation.id)
        self.assertIsNone(self.conv_repo.get_by_id(self.conversation.id))


class AIServiceTest(BaseAITest):
    def setUp(self):
        super().setUp()
        AIProvider.objects.create(name='openai', api_key='sk-test', is_active=True)
        self.service = AIService()

    def test_create_conversation(self):
        result = self.service.create_conversation(self.user.id, 'Service Test')
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['conversation'])

    def test_get_user_conversations(self):
        AIConversation.objects.create(user=self.user, title='C1')
        qs = self.service.get_user_conversations(self.user.id)
        self.assertEqual(qs.count(), 1)

    def test_delete_conversation(self):
        conv = AIConversation.objects.create(user=self.user, title='To Delete')
        result = self.service.delete_conversation(conv.id, self.user.id)
        self.assertTrue(result['success'])

    def test_delete_conversation_wrong_user(self):
        other = User.objects.create_user(username='other', password='test1234')
        conv = AIConversation.objects.create(user=other, title='Other')
        result = self.service.delete_conversation(conv.id, self.user.id)
        self.assertFalse(result['success'])

    def test_get_conversation_history_not_found(self):
        result = self.service.get_conversation_history(999, self.user.id)
        self.assertFalse(result['success'])

    def test_send_message_no_active_provider(self):
        AIProvider.objects.all().update(is_active=False)
        conv = AIConversation.objects.create(user=self.user, title='Test')
        result = self.service.send_message(conv.id, self.user.id, 'Hello')
        self.assertFalse(result['success'])


class AIViewsTest(BaseAITest):
    def setUp(self):
        super().setUp()
        AIProvider.objects.create(name='openai', api_key='sk-test', is_active=True)
        self.conversation = AIConversation.objects.create(user=self.user, title='Test Chat')

    def test_chat_view_requires_login(self):
        response = self.client.get(reverse('ai_assistant:chat'))
        self.assertNotEqual(response.status_code, 200)

    def test_chat_view_authenticated(self):
        self.client.login(username='testuser', password='test1234')
        response = self.client.get(reverse('ai_assistant:chat'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ai_assistant/ai_chat.html')

    def test_history_view(self):
        self.client.login(username='testuser', password='test1234')
        response = self.client.get(reverse('ai_assistant:history'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ai_assistant/ai_history.html')

    def test_sidebar_view(self):
        self.client.login(username='testuser', password='test1234')
        response = self.client.get(reverse('ai_assistant:sidebar'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ai_assistant/ai_sidebar.html')

    def test_new_conversation(self):
        self.client.login(username='testuser', password='test1234')
        response = self.client.post(reverse('ai_assistant:new_conversation'), {
            'title': 'New Chat'
        })
        self.assertIn(response.status_code, [200, 302])

    def test_delete_conversation(self):
        self.client.login(username='testuser', password='test1234')
        response = self.client.post(
            reverse('ai_assistant:delete_conversation', args=[self.conversation.id])
        )
        self.assertIn(response.status_code, [200, 302])
        self.assertFalse(AIConversation.objects.filter(id=self.conversation.id).exists())

    def test_send_message_no_content(self):
        self.client.login(username='testuser', password='test1234')
        response = self.client.post(reverse('ai_assistant:send_message'), {'message': ''})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])

    def test_summarize_empty(self):
        self.client.login(username='testuser', password='test1234')
        response = self.client.post(reverse('ai_assistant:summarize'), {'text': ''})
        data = response.json()
        self.assertFalse(data['success'])

    def test_ask_empty(self):
        self.client.login(username='testuser', password='test1234')
        response = self.client.post(reverse('ai_assistant:ask_question'), {'question': ''})
        data = response.json()
        self.assertFalse(data['success'])

    def test_recommendations(self):
        self.client.login(username='testuser', password='test1234')
        response = self.client.post(reverse('ai_assistant:recommendations'), {
            'interests': 'Pemrograman'
        })
        self.assertEqual(response.status_code, 200)


class AIURLTest(BaseAITest):
    def test_chat_url(self):
        self.assertEqual(reverse('ai_assistant:chat'), '/ai/')

    def test_send_url(self):
        self.assertEqual(reverse('ai_assistant:send_message'), '/ai/send/')

    def test_history_url(self):
        self.assertEqual(reverse('ai_assistant:history'), '/ai/history/')

    def test_new_conversation_url(self):
        self.assertEqual(reverse('ai_assistant:new_conversation'), '/ai/new/')

    def test_summarize_url(self):
        self.assertEqual(reverse('ai_assistant:summarize'), '/ai/summarize/')

    def test_recommendations_url(self):
        self.assertEqual(reverse('ai_assistant:recommendations'), '/ai/recommendations/')

    def test_ask_url(self):
        self.assertEqual(reverse('ai_assistant:ask_question'), '/ai/ask/')
