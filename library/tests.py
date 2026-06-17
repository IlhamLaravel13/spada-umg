from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from academics.models import Faculty, StudyProgram
from .models import LibraryCategory, LibraryItem
from .services import LibraryService
from .repositories import LibraryItemRepository, LibraryCategoryRepository

User = get_user_model()


class BaseLibraryTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', email='test@umg.ac.id',
            password='test1234', role='admin',
            first_name='Test', last_name='User',
        )
        self.mahasiswa = User.objects.create_user(
            username='mhs', email='mhs@umg.ac.id',
            password='test1234', role='mahasiswa', nim='2024001',
        )
        faculty = Faculty.objects.create(name='FT', code='FT')
        prodi = StudyProgram.objects.create(faculty=faculty, name='TI', code='TI', degree='s1')
        self.category = LibraryCategory.objects.create(name='E-Book', slug='ebook')
        self.item = LibraryItem.objects.create(
            title='Test Book', author='Test Author', item_type='ebook',
            category=self.category, faculty=faculty, study_program=prodi,
            file=SimpleUploadedFile('test.pdf', b'file_content', content_type='application/pdf'),
            uploaded_by=self.user, is_published=True,
        )


class LibraryModelTest(BaseLibraryTest):
    def test_category_creation(self):
        self.assertEqual(self.category.name, 'E-Book')
        self.assertEqual(str(self.category), 'E-Book')

    def test_item_creation(self):
        self.assertEqual(self.item.title, 'Test Book')
        self.assertEqual(self.item.author, 'Test Author')
        self.assertEqual(self.item.item_type, 'ebook')
        self.assertTrue(self.item.is_published)
        self.assertEqual(str(self.item), 'Test Book')

    def test_item_ordering(self):
        item2 = LibraryItem.objects.create(
            title='Second', author='Author', item_type='journal',
            file=SimpleUploadedFile('test2.pdf', b'content', content_type='application/pdf'),
            uploaded_by=self.user, is_published=True,
        )
        qs = LibraryItem.objects.all()
        self.assertEqual(qs.first(), item2)


class LibraryRepositoryTest(BaseLibraryTest):
    def setUp(self):
        super().setUp()
        self.repo = LibraryItemRepository()
        self.cat_repo = LibraryCategoryRepository()

    def test_get_published(self):
        self.assertEqual(self.repo.get_published().count(), 1)

    def test_get_by_id(self):
        item = self.repo.get_by_id(self.item.id)
        self.assertIsNotNone(item)
        self.assertEqual(item.title, 'Test Book')

    def test_get_by_category(self):
        qs = self.repo.get_by_category(self.category.id)
        self.assertEqual(qs.count(), 1)

    def test_get_by_type(self):
        qs = self.repo.get_by_type('ebook')
        self.assertEqual(qs.count(), 1)

    def test_search(self):
        qs = self.repo.search('Test')
        self.assertEqual(qs.count(), 1)
        qs = self.repo.search('Nonexistent')
        self.assertEqual(qs.count(), 0)

    def test_create_item(self):
        item = self.repo.create_item(
            title='New', author='New Author', item_type='module',
            file=SimpleUploadedFile('new.pdf', b'x', content_type='application/pdf'),
            uploaded_by=self.user,
        )
        self.assertEqual(item.title, 'New')

    def test_update_item(self):
        result = self.repo.update_item(self.item.id, title='Updated Title')
        self.assertIsNotNone(result)
        self.assertEqual(result.title, 'Updated Title')

    def test_delete_item(self):
        self.repo.delete_item(self.item.id)
        self.assertIsNone(self.repo.get_by_id(self.item.id))

    def test_category_repo_active(self):
        qs = self.cat_repo.get_active()
        self.assertEqual(qs.count(), 1)


class LibraryServiceTest(BaseLibraryTest):
    def setUp(self):
        super().setUp()
        self.service = LibraryService()

    def test_increment_view(self):
        old = self.item.view_count
        self.service.increment_view(self.item.id)
        self.item.refresh_from_db()
        self.assertEqual(self.item.view_count, old + 1)

    def test_increment_download(self):
        old = self.item.download_count
        self.service.increment_download(self.item.id)
        self.item.refresh_from_db()
        self.assertEqual(self.item.download_count, old + 1)

    def test_get_categories_with_count(self):
        cats = self.service.get_categories_with_count()
        self.assertEqual(cats.count(), 1)

    def test_delete_item(self):
        result = self.service.delete_item(self.item.id, self.user)
        self.assertTrue(result['success'])


class LibraryViewsTest(BaseLibraryTest):
    def test_library_list(self):
        self.client.login(username='mhs', password='test1234')
        response = self.client.get(reverse('library:list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'library/library_list.html')

    def test_library_detail(self):
        self.client.login(username='mhs', password='test1234')
        response = self.client.get(reverse('library:detail', args=[self.item.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'library/library_detail.html')

    def test_library_download(self):
        self.client.login(username='mhs', password='test1234')
        response = self.client.get(reverse('library:download', args=[self.item.id]))
        self.assertIn(response.status_code, [200, 302])

    def test_library_upload_view(self):
        self.client.login(username='testuser', password='test1234')
        response = self.client.get(reverse('library:upload'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'library/library_form.html')

    def test_library_category_list(self):
        self.client.login(username='mhs', password='test1234')
        response = self.client.get(reverse('library:category_list'))
        self.assertEqual(response.status_code, 200)

    def test_library_delete(self):
        self.client.login(username='testuser', password='test1234')
        response = self.client.post(reverse('library:delete', args=[self.item.id]))
        self.assertEqual(LibraryItem.objects.filter(id=self.item.id).count(), 0)


class LibraryURLTest(BaseLibraryTest):
    def test_list_url(self):
        self.assertEqual(reverse('library:list'), '/library/')

    def test_detail_url(self):
        self.assertEqual(reverse('library:detail', args=[1]), '/library/1/')

    def test_download_url(self):
        self.assertEqual(reverse('library:download', args=[1]), '/library/1/download/')

    def test_upload_url(self):
        self.assertEqual(reverse('library:upload'), '/library/upload/')

    def test_category_list_url(self):
        self.assertEqual(reverse('library:category_list'), '/library/categories/')
