from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import Forum, ForumTopic, ForumReply
from academics.models import Faculty, StudyProgram, AcademicYear, Semester, Course, Class as ClassModel

User = get_user_model()


class BaseForumTest(TestCase):
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
        faculty = Faculty.objects.create(name='FT', code='FT')
        sp = StudyProgram.objects.create(faculty=faculty, name='TI', code='TI', degree='s1')
        course = Course.objects.create(study_program=sp, code='CS101', name='Algoritma', credits=3, semester=1)
        ay = AcademicYear.objects.create(year='2024/2025', start_date='2024-09-01', end_date='2025-08-31')
        semester = Semester.objects.create(academic_year=ay, name='Ganjil 2024', code='G2024', start_date='2024-09-01', end_date='2025-01-31')
        self.class_obj = ClassModel.objects.create(
            course=course, semester=semester, name='A', code='CS101-A',
            lecturer=self.dosen, max_students=40,
        )
        self.forum = Forum.objects.create(
            class_meta=self.class_obj,
            title='Forum Test',
            description='Deskripsi forum',
            created_by=self.admin,
        )

    def _create_topic(self, **kwargs):
        data = {
            'forum': self.forum,
            'title': 'Topik Test',
            'content': 'Konten topik test.',
            'author': self.mahasiswa,
        }
        data.update(kwargs)
        return ForumTopic.objects.create(**data)

    def _create_reply(self, **kwargs):
        topic = kwargs.pop('topic', None) or self._create_topic()
        data = {
            'topic': topic,
            'content': 'Balasan test.',
            'author': self.mahasiswa,
        }
        data.update(kwargs)
        return ForumReply.objects.create(**data)


class ForumModelTest(BaseForumTest):
    def test_create_forum(self):
        self.assertEqual(self.forum.title, 'Forum Test')
        self.assertTrue(self.forum.is_active)
        self.assertEqual(str(self.forum), 'Forum Test')

    def test_forum_ordering(self):
        f2 = Forum.objects.create(class_meta=self.class_obj, title='F2', created_by=self.admin)
        qs = Forum.objects.all()
        self.assertEqual(qs.first(), f2)


class ForumTopicModelTest(BaseForumTest):
    def test_create_topic(self):
        topic = self._create_topic()
        self.assertEqual(topic.title, 'Topik Test')
        self.assertEqual(str(topic), 'Topik Test')
        self.assertEqual(topic.views, 0)

    def test_topic_ordering(self):
        t1 = self._create_topic(title='A', is_pinned=False)
        t2 = self._create_topic(title='B', is_pinned=True)
        qs = ForumTopic.objects.all()
        self.assertEqual(qs.first(), t2)


class ForumReplyModelTest(BaseForumTest):
    def test_create_reply(self):
        reply = self._create_reply()
        self.assertIn('Balasan', str(reply))

    def test_nested_reply(self):
        topic = self._create_topic()
        parent = ForumReply.objects.create(topic=topic, content='Parent', author=self.mahasiswa)
        child = ForumReply.objects.create(topic=topic, content='Child', author=self.mahasiswa, parent=parent)
        self.assertEqual(child.parent, parent)
        self.assertIn(parent, parent.replies.all())

    def test_solution_flag(self):
        reply = self._create_reply(is_solution=True)
        self.assertTrue(reply.is_solution)


class ForumViewsTest(BaseForumTest):
    def test_forum_list(self):
        response = self.client.get(reverse('forum:forum_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'forum/forum_list.html')

    def test_forum_detail(self):
        response = self.client.get(reverse('forum:forum_detail', args=[self.forum.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'forum/forum_detail.html')

    def test_topic_detail(self):
        topic = self._create_topic()
        response = self.client.get(reverse('forum:topic_detail', args=[topic.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'forum/topic_detail.html')

    def test_create_topic_requires_login(self):
        response = self.client.get(reverse('forum:topic_create', args=[self.forum.id]))
        self.assertNotEqual(response.status_code, 200)

    def test_create_topic_authenticated(self):
        self.client.login(username='mhs1', password='test123')
        response = self.client.get(reverse('forum:topic_create', args=[self.forum.id]))
        self.assertEqual(response.status_code, 200)

    def test_create_topic_post(self):
        self.client.login(username='mhs1', password='test123')
        response = self.client.post(reverse('forum:topic_create', args=[self.forum.id]), {
            'title': 'Topik Baru',
            'content': 'Konten baru.',
        })
        self.assertIn(response.status_code, [200, 302])
        self.assertTrue(ForumTopic.objects.filter(title='Topik Baru').exists())

    def test_create_reply(self):
        self.client.login(username='mhs1', password='test123')
        topic = self._create_topic()
        response = self.client.post(reverse('forum:reply_create', args=[topic.id]), {
            'content': 'Balasan baru.',
        })
        self.assertIn(response.status_code, [200, 302])
        self.assertTrue(ForumReply.objects.filter(content='Balasan baru.').exists())

    def test_toggle_like(self):
        self.client.login(username='mhs1', password='test123')
        reply = self._create_reply()
        response = self.client.post(reverse('forum:reply_toggle_like', args=[reply.id]))
        self.assertIn(response.status_code, [200, 302])
        self.assertTrue(reply.likes.filter(id=self.mahasiswa.id).exists())

    def test_mark_solution(self):
        self.client.login(username='dosen1', password='test123')
        topic = self._create_topic()
        reply = self._create_reply(topic=topic)
        response = self.client.post(reverse('forum:reply_mark_solution', args=[reply.id, topic.id]))
        self.assertIn(response.status_code, [200, 302])
        reply.refresh_from_db()
        self.assertTrue(reply.is_solution)


class ForumServiceTest(BaseForumTest):
    def test_service_create_forum(self):
        from .services import ForumService
        service = ForumService()
        result = service.create(
            class_meta=self.class_obj, title='Service Test',
            description='Test', created_by=self.admin,
        )
        self.assertTrue(result['success'])
        self.assertIsNotNone(service.get_by_id(result['data'].id))

    def test_service_create_topic(self):
        from .services import ForumService
        service = ForumService()
        result = service.create_topic(
            forum=self.forum, title='Topic Svc',
            content='Content', author=self.mahasiswa,
        )
        self.assertTrue(result['success'])

    def test_service_create_reply(self):
        from .services import ForumService
        service = ForumService()
        topic = self._create_topic()
        result = service.create_reply(
            topic=topic, content='Reply Svc', author=self.mahasiswa,
        )
        self.assertTrue(result['success'])

    def test_service_toggle_like(self):
        from .services import ForumService
        service = ForumService()
        reply = self._create_reply()
        result = service.toggle_like(reply.id, self.mahasiswa)
        self.assertTrue(result['success'])
        self.assertTrue(result['liked'])

    def test_service_mark_solution(self):
        from .services import ForumService
        service = ForumService()
        topic = self._create_topic()
        reply = self._create_reply(topic=topic)
        result = service.mark_as_solution(reply.id, topic.id)
        self.assertTrue(result['success'])
