from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Announcement, AnnouncementRead
from academics.models import Faculty, StudyProgram, AcademicYear, Semester, Course, Class as ClassModel

User = get_user_model()


class BaseAnnouncementTest(TestCase):
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

    def _create_announcement(self, **kwargs):
        data = {
            'title': 'Pengumuman Test',
            'content': 'Ini adalah konten pengumuman test.',
            'category': 'umum',
            'audience': 'all',
            'is_published': True,
            'is_important': False,
            'created_by': self.admin,
        }
        data.update(kwargs)
        return Announcement.objects.create(**data)


class AnnouncementModelTest(BaseAnnouncementTest):
    def test_create_announcement(self):
        ann = self._create_announcement()
        self.assertEqual(ann.title, 'Pengumuman Test')
        self.assertTrue(ann.is_published)
        self.assertEqual(str(ann), 'Pengumuman Test')

    def test_important_ordering(self):
        a1 = self._create_announcement(title='Biasa', is_important=False)
        a2 = self._create_announcement(title='Penting', is_important=True)
        qs = Announcement.objects.all()
        self.assertEqual(qs.first(), a2)


class AnnouncementReadModelTest(BaseAnnouncementTest):
    def test_mark_as_read(self):
        ann = self._create_announcement()
        read = AnnouncementRead.objects.create(announcement=ann, user=self.mahasiswa)
        self.assertEqual(read.announcement, ann)
        self.assertEqual(read.user, self.mahasiswa)

    def test_unique_together(self):
        ann = self._create_announcement()
        AnnouncementRead.objects.create(announcement=ann, user=self.mahasiswa)
        with self.assertRaises(Exception):
            AnnouncementRead.objects.create(announcement=ann, user=self.mahasiswa)


class AnnouncementViewsTest(BaseAnnouncementTest):
    def test_list_public(self):
        self._create_announcement()
        response = self.client.get(reverse('announcements:announcement_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'announcements/announcement_list.html')

    def test_list_authenticated(self):
        self.client.login(username='mhs1', password='test123')
        self._create_announcement()
        response = self.client.get(reverse('announcements:announcement_list'))
        self.assertEqual(response.status_code, 200)

    def test_detail(self):
        ann = self._create_announcement()
        response = self.client.get(reverse('announcements:announcement_detail', args=[ann.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'announcements/announcement_detail.html')

    def test_create_requires_admin(self):
        self.client.login(username='mhs1', password='test123')
        response = self.client.get(reverse('announcements:announcement_create'))
        self.assertNotEqual(response.status_code, 200)

    def test_create_by_admin(self):
        self.client.login(username='admin1', password='test123')
        response = self.client.get(reverse('announcements:announcement_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'announcements/announcement_form.html')

    def test_create_post(self):
        self.client.login(username='admin1', password='test123')
        response = self.client.post(reverse('announcements:announcement_create'), {
            'title': 'Pengumuman Baru',
            'content': 'Konten baru',
            'category': 'umum',
            'audience': 'all',
            'is_published': True,
            'is_important': False,
        })
        self.assertIn(response.status_code, [200, 302])
        self.assertTrue(Announcement.objects.filter(title='Pengumuman Baru').exists())

    def test_delete(self):
        self.client.login(username='admin1', password='test123')
        ann = self._create_announcement()
        response = self.client.post(reverse('announcements:announcement_delete', args=[ann.id]))
        self.assertIn(response.status_code, [200, 302])
        self.assertFalse(Announcement.objects.filter(id=ann.id).exists())

    def test_mark_as_read(self):
        self.client.login(username='mhs1', password='test123')
        ann = self._create_announcement()
        response = self.client.post(reverse('announcements:announcement_mark_read', args=[ann.id]))
        self.assertIn(response.status_code, [200, 302])
        self.assertTrue(AnnouncementRead.objects.filter(announcement=ann, user=self.mahasiswa).exists())

    def test_banner(self):
        self._create_announcement(is_important=True)
        response = self.client.get(reverse('announcements:announcement_banner'))
        self.assertEqual(response.status_code, 200)


class AnnouncementServiceTest(BaseAnnouncementTest):
    def test_create_and_get(self):
        from .services import AnnouncementService
        service = AnnouncementService()
        result = service.create(
            title='Service Test',
            content='Content',
            created_by=self.admin,
        )
        self.assertTrue(result['success'])
        self.assertIsNotNone(service.get_by_id(result['data'].id))

    def test_unread_count(self):
        from .services import AnnouncementService
        service = AnnouncementService()
        ann = self._create_announcement()
        count = service.get_unread_count(self.mahasiswa)
        self.assertEqual(count, 1)
        service.mark_as_read(self.mahasiswa, ann.id)
        count = service.get_unread_count(self.mahasiswa)
        self.assertEqual(count, 0)

    def test_mark_all_as_read(self):
        from .services import AnnouncementService
        service = AnnouncementService()
        self._create_announcement(title='A1')
        self._create_announcement(title='A2')
        service.mark_all_as_read(self.mahasiswa)
        self.assertEqual(service.get_unread_count(self.mahasiswa), 0)

    def test_get_for_user_mahasiswa(self):
        from .services import AnnouncementService
        service = AnnouncementService()
        self._create_announcement(audience='all')
        self._create_announcement(audience='mahasiswa')
        self._create_announcement(audience='dosen')
        qs = service.get_for_user(self.mahasiswa)
        self.assertEqual(qs.count(), 2)
