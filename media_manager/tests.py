from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import MediaFile

User = get_user_model()


class BaseMediaTest(TestCase):
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
        self.media_file = MediaFile.objects.create(
            title='Test Image',
            description='A test image',
            file_type='image',
            mime_type='image/png',
            file_size=1024,
            uploaded_by=self.admin,
            is_public=True,
        )

    def _upload_file(self):
        return SimpleUploadedFile(
            'test.png',
            b'fake-png-content',
            content_type='image/png'
        )


class MediaFileModelTest(BaseMediaTest):
    def test_create_media_file(self):
        self.assertEqual(self.media_file.title, 'Test Image')
        self.assertEqual(str(self.media_file), 'Test Image')
        self.assertTrue(self.media_file.is_public)

    def test_media_ordering(self):
        m2 = MediaFile.objects.create(
            title='Second', file_type='document',
            mime_type='application/pdf', file_size=2048,
            uploaded_by=self.admin,
        )
        qs = MediaFile.objects.all()
        self.assertEqual(qs.first(), m2)

    def test_file_type_choices(self):
        self.assertIn(self.media_file.file_type, dict(MediaFile.FILE_TYPE_CHOICES))


class MediaFileViewsTest(BaseMediaTest):
    def test_media_list(self):
        response = self.client.get(reverse('media_manager:media_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'media_manager/media_list.html')

    def test_media_detail(self):
        response = self.client.get(reverse('media_manager:media_detail', args=[self.media_file.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'media_manager/media_detail.html')

    def test_media_list_filter_type(self):
        response = self.client.get(reverse('media_manager:media_list'), {'type': 'image'})
        self.assertEqual(response.status_code, 200)

    def test_media_list_search(self):
        response = self.client.get(reverse('media_manager:media_list'), {'q': 'Test'})
        self.assertEqual(response.status_code, 200)

    def test_upload_requires_login(self):
        response = self.client.get(reverse('media_manager:media_upload'))
        self.assertNotEqual(response.status_code, 200)

    def test_upload_authenticated(self):
        self.client.login(username='admin1', password='test123')
        response = self.client.get(reverse('media_manager:media_upload'))
        self.assertEqual(response.status_code, 200)

    def test_upload_post(self):
        self.client.login(username='admin1', password='test123')
        uploaded = self._upload_file()
        response = self.client.post(reverse('media_manager:media_upload'), {
            'title': 'New Upload',
            'file': uploaded,
            'file_type': 'image',
        })
        self.assertIn(response.status_code, [200, 302])
        self.assertTrue(MediaFile.objects.filter(title='New Upload').exists())

    def test_delete_requires_login(self):
        response = self.client.post(reverse('media_manager:media_delete', args=[self.media_file.id]))
        self.assertNotEqual(response.status_code, 200)

    def test_delete_owner(self):
        self.client.login(username='admin1', password='test123')
        response = self.client.post(reverse('media_manager:media_delete', args=[self.media_file.id]))
        self.assertIn(response.status_code, [200, 302])
        self.assertFalse(MediaFile.objects.filter(id=self.media_file.id).exists())


class MediaFileServiceTest(BaseMediaTest):
    def test_service_upload(self):
        from .services import MediaFileService
        service = MediaFileService()
        uploaded = self._upload_file()
        result = service.upload(
            title='Service Upload',
            file=uploaded,
            file_type='image',
            uploaded_by=self.admin,
        )
        self.assertTrue(result['success'])
        self.assertIsNotNone(service.get_by_id(result['data'].id))

    def test_service_update(self):
        from .services import MediaFileService
        service = MediaFileService()
        result = service.update(self.media_file.id, title='Updated Title')
        self.assertTrue(result['success'])
        self.assertEqual(result['data'].title, 'Updated Title')

    def test_service_delete(self):
        from .services import MediaFileService
        service = MediaFileService()
        result = service.delete(self.media_file.id)
        self.assertTrue(result['success'])

    def test_service_increment_download(self):
        from .services import MediaFileService
        service = MediaFileService()
        result = service.increment_download(self.media_file.id)
        self.assertTrue(result['success'])
        self.media_file.refresh_from_db()
        self.assertEqual(self.media_file.download_count, 1)
