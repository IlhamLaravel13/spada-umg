from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from academics.models import (
    Faculty, StudyProgram, AcademicYear, Semester, Course, Class, Enrollment
)
from .models import Material, MaterialComment, CourseProgress
from .services import MaterialService, CourseProgressService
from .repositories import (
    MaterialRepository, MaterialCommentRepository, CourseProgressRepository
)

User = get_user_model()


class BaseTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.dosen = User.objects.create_user(
            username='dosen1', email='dosen@umg.ac.id',
            password='test1234', role='dosen', nidn='1234567890',
            first_name='Dosen', last_name='Satu'
        )
        self.mahasiswa = User.objects.create_user(
            username='mhs1', email='mhs@umg.ac.id',
            password='test1234', role='mahasiswa', nim='2024001',
            first_name='Mahasiswa', last_name='Satu'
        )
        self.admin = User.objects.create_user(
            username='admin1', email='admin@umg.ac.id',
            password='test1234', role='admin',
            is_staff=True, is_superuser=True
        )

        faculty = Faculty.objects.create(name='FT', code='FT')
        prodi = StudyProgram.objects.create(
            faculty=faculty, name='TI', code='TI',
            degree='s1'
        )
        year = AcademicYear.objects.create(
            year='2024/2025', start_date='2024-09-01',
            end_date='2025-08-31'
        )
        semester = Semester.objects.create(
            academic_year=year, name='Ganjil 2024/2025',
            code='G2024', start_date='2024-09-01',
            end_date='2025-01-31', is_active=True
        )
        course = Course.objects.create(
            study_program=prodi, code='TI101', name='Pemrograman',
            credits=3, semester=1
        )
        self.class_obj = Class.objects.create(
            course=course, semester=semester, name='A',
            code='TI101-A', lecturer=self.dosen
        )
        Enrollment.objects.create(
            student=self.mahasiswa, class_enrolled=self.class_obj, status='active'
        )

        self.material = Material.objects.create(
            class_meta=self.class_obj, title='Bab 1',
            file_type='pdf', uploaded_by=self.dosen
        )


class MaterialModelTest(BaseTest):
    def test_material_creation(self):
        self.assertEqual(self.material.title, 'Bab 1')
        self.assertEqual(self.material.file_type, 'pdf')
        self.assertTrue(self.material.is_published)
        self.assertTrue(self.material.allow_download)

    def test_material_str(self):
        self.assertEqual(str(self.material), 'Bab 1')

    def test_material_ordering(self):
        m2 = Material.objects.create(
            class_meta=self.class_obj, title='Bab 0',
            file_type='pdf', uploaded_by=self.dosen, order=1
        )
        qs = Material.objects.filter(class_meta=self.class_obj)
        self.assertGreater(m2.order, self.material.order)


class MaterialCommentModelTest(BaseTest):
    def test_comment_creation(self):
        comment = MaterialComment.objects.create(
            material=self.material, user=self.mahasiswa,
            comment='Terima kasih'
        )
        self.assertEqual(comment.comment, 'Terima kasih')
        self.assertEqual(comment.user, self.mahasiswa)

    def test_comment_str(self):
        comment = MaterialComment.objects.create(
            material=self.material, user=self.mahasiswa,
            comment='Mantap'
        )
        self.assertIn('Mahasiswa', str(comment))


class CourseProgressModelTest(BaseTest):
    def test_progress_creation(self):
        progress = CourseProgress.objects.create(
            student=self.mahasiswa, class_meta=self.class_obj,
            material=self.material, is_completed=True
        )
        self.assertTrue(progress.is_completed)
        self.assertEqual(progress.student, self.mahasiswa)

    def test_progress_unique_together(self):
        CourseProgress.objects.create(
            student=self.mahasiswa, class_meta=self.class_obj,
            material=self.material
        )
        with self.assertRaises(Exception):
            CourseProgress.objects.create(
                student=self.mahasiswa, class_meta=self.class_obj,
                material=self.material
            )


class MaterialRepositoryTest(BaseTest):
    def setUp(self):
        super().setUp()
        self.repo = MaterialRepository()

    def test_get_by_id(self):
        material = self.repo.get_by_id(self.material.id)
        self.assertIsNotNone(material)
        self.assertEqual(material.title, 'Bab 1')

    def test_get_by_class(self):
        qs = self.repo.get_by_class(self.class_obj.id)
        self.assertEqual(qs.count(), 1)

    def test_get_published_by_class(self):
        qs = self.repo.get_published_by_class(self.class_obj.id)
        self.assertEqual(qs.count(), 1)

    def test_search(self):
        qs = self.repo.search(self.class_obj.id, 'Bab')
        self.assertEqual(qs.count(), 1)
        qs = self.repo.search(self.class_obj.id, 'XYZ')
        self.assertEqual(qs.count(), 0)

    def test_create_material(self):
        m = self.repo.create_material(
            class_meta=self.class_obj, title='New',
            file_type='pdf', uploaded_by=self.dosen
        )
        self.assertEqual(m.title, 'New')

    def test_update_material(self):
        result = self.repo.update_material(self.material.id, title='Updated')
        self.assertIsNotNone(result)
        self.assertEqual(result.title, 'Updated')

    def test_delete_material(self):
        mid = self.material.id
        self.repo.delete_material(mid)
        self.assertIsNone(self.repo.get_by_id(mid))


class MaterialCommentRepositoryTest(BaseTest):
    def setUp(self):
        super().setUp()
        self.repo = MaterialCommentRepository()

    def test_create_comment(self):
        comment = self.repo.create_comment(
            self.material.id, self.mahasiswa.id, 'Bagus'
        )
        self.assertEqual(comment.comment, 'Bagus')

    def test_get_for_material(self):
        self.repo.create_comment(self.material.id, self.mahasiswa.id, 'Komentar 1')
        qs = self.repo.get_for_material(self.material.id)
        self.assertEqual(qs.count(), 1)


class CourseProgressRepositoryTest(BaseTest):
    def setUp(self):
        super().setUp()
        self.repo = CourseProgressRepository()

    def test_mark_completed(self):
        progress = self.repo.mark_completed(
            self.mahasiswa.id, self.material.id, self.class_obj.id
        )
        self.assertTrue(progress.is_completed)

    def test_is_completed(self):
        self.assertFalse(self.repo.is_completed(self.mahasiswa.id, self.material.id))
        self.repo.mark_completed(
            self.mahasiswa.id, self.material.id, self.class_obj.id
        )
        self.assertTrue(self.repo.is_completed(self.mahasiswa.id, self.material.id))

    def test_get_completed_count(self):
        self.assertEqual(
            self.repo.get_completed_count(self.mahasiswa.id, self.class_obj.id), 0
        )
        self.repo.mark_completed(
            self.mahasiswa.id, self.material.id, self.class_obj.id
        )
        self.assertEqual(
            self.repo.get_completed_count(self.mahasiswa.id, self.class_obj.id), 1
        )

    def test_mark_incomplete(self):
        self.repo.mark_completed(
            self.mahasiswa.id, self.material.id, self.class_obj.id
        )
        self.repo.mark_incomplete(self.mahasiswa.id, self.material.id)
        self.assertFalse(self.repo.is_completed(self.mahasiswa.id, self.material.id))


class MaterialServiceTest(BaseTest):
    def setUp(self):
        super().setUp()
        self.service = MaterialService()

    def test_get_class_materials_mahasiswa(self):
        qs = self.service.get_class_materials(self.class_obj.id)
        self.assertEqual(qs.count(), 1)

    def test_toggle_publish(self):
        result = self.service.toggle_publish(self.material.id)
        self.assertTrue(result['success'])
        self.assertFalse(result['is_published'])

    def test_add_comment(self):
        result = self.service.add_comment(
            self.material.id, self.mahasiswa.id, 'Keren'
        )
        self.assertTrue(result['success'])

    def test_add_comment_empty(self):
        result = self.service.add_comment(
            self.material.id, self.mahasiswa.id, ''
        )
        self.assertFalse(result['success'])


class CourseProgressServiceTest(BaseTest):
    def setUp(self):
        super().setUp()
        self.service = CourseProgressService()

    def test_get_completion_stats(self):
        stats = self.service.get_completion_stats(
            self.mahasiswa.id, self.class_obj.id
        )
        self.assertEqual(stats['total'], 1)
        self.assertEqual(stats['completed'], 0)
        self.assertEqual(stats['percentage'], 0)

    def test_mark_completed(self):
        result = self.service.mark_completed(
            self.mahasiswa.id, self.material.id, self.class_obj.id
        )
        self.assertTrue(result['success'])
        stats = self.service.get_completion_stats(
            self.mahasiswa.id, self.class_obj.id
        )
        self.assertEqual(stats['completed'], 1)
        self.assertEqual(stats['percentage'], 100)


class ViewsTest(BaseTest):
    def test_course_list_mahasiswa(self):
        self.client.login(username='mhs1', password='test1234')
        response = self.client.get(reverse('courses:course_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courses/course_list.html')

    def test_course_list_dosen(self):
        self.client.login(username='dosen1', password='test1234')
        response = self.client.get(reverse('courses:course_list'))
        self.assertEqual(response.status_code, 200)

    def test_course_detail_mahasiswa(self):
        self.client.login(username='mhs1', password='test1234')
        response = self.client.get(
            reverse('courses:course_detail', kwargs={'pk': self.class_obj.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courses/course_detail.html')

    def test_my_courses_dosen(self):
        self.client.login(username='dosen1', password='test1234')
        response = self.client.get(reverse('courses:my_courses'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courses/my_courses.html')

    def test_my_courses_mahasiswa_denied(self):
        self.client.login(username='mhs1', password='test1234')
        response = self.client.get(reverse('courses:my_courses'))
        self.assertEqual(response.status_code, 302)

    def test_material_manage_dosen(self):
        self.client.login(username='dosen1', password='test1234')
        response = self.client.get(
            reverse('courses:material_manage', kwargs={'class_id': self.class_obj.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courses/material_list.html')

    def test_material_upload_view(self):
        self.client.login(username='dosen1', password='test1234')
        response = self.client.get(
            reverse('courses:material_upload', kwargs={'class_id': self.class_obj.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courses/material_form.html')

    def test_material_detail(self):
        self.client.login(username='mhs1', password='test1234')
        response = self.client.get(
            reverse('courses:material_detail', kwargs={'pk': self.material.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courses/material_detail.html')

    def test_material_detail_unpublished_mahasiswa(self):
        self.material.is_published = False
        self.material.save()
        self.client.login(username='mhs1', password='test1234')
        response = self.client.get(
            reverse('courses:material_detail', kwargs={'pk': self.material.id})
        )
        self.assertEqual(response.status_code, 404)

    def test_toggle_publish(self):
        self.client.login(username='dosen1', password='test1234')
        response = self.client.post(
            reverse('courses:material_toggle_publish', kwargs={'pk': self.material.id})
        )
        self.assertIn(response.status_code, [200, 302])

    def test_add_comment(self):
        self.client.login(username='mhs1', password='test1234')
        response = self.client.post(
            reverse('courses:material_comment', kwargs={'pk': self.material.id}),
            {'comment': 'Bagus sekali'}
        )
        comment_count = MaterialComment.objects.filter(material=self.material).count()
        self.assertEqual(comment_count, 1)

    def test_mark_complete(self):
        self.client.login(username='mhs1', password='test1234')
        response = self.client.post(
            reverse(
                'courses:mark_complete',
                kwargs={
                    'class_id': self.class_obj.id,
                    'material_id': self.material.id
                }
            )
        )
        self.assertTrue(
            CourseProgress.objects.filter(
                student=self.mahasiswa, material=self.material, is_completed=True
            ).exists()
        )

    def test_material_delete(self):
        self.client.login(username='dosen1', password='test1234')
        response = self.client.post(
            reverse('courses:material_delete', kwargs={'pk': self.material.id})
        )
        self.assertEqual(Material.objects.filter(id=self.material.id).count(), 0)


class URLTest(BaseTest):
    def test_course_list_url(self):
        self.assertEqual(reverse('courses:course_list'), '/courses/')

    def test_my_courses_url(self):
        self.assertEqual(reverse('courses:my_courses'), '/courses/my-courses/')

    def test_material_manage_url(self):
        url = reverse(
            'courses:material_manage',
            kwargs={'class_id': self.class_obj.id}
        )
        self.assertEqual(url, f'/courses/{self.class_obj.id}/materials/manage/')

    def test_material_upload_url(self):
        url = reverse(
            'courses:material_upload',
            kwargs={'class_id': self.class_obj.id}
        )
        self.assertEqual(url, f'/courses/{self.class_obj.id}/materials/upload/')
