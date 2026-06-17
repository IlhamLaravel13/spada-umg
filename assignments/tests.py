from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models import Assignment, AssignmentSubmission, AssignmentSubmissionAttachment
from academics.models import Faculty, StudyProgram, AcademicYear, Semester, Course, Class

User = get_user_model()


class AssignmentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='dosen1', password='test1234', role='dosen')
        self.student = User.objects.create_user(username='student1', password='test1234', role='mahasiswa')
        faculty = Faculty.objects.create(name='FT', code='FT')
        sp = StudyProgram.objects.create(faculty=faculty, name='IF', code='IF', degree='s1')
        course = Course.objects.create(study_program=sp, code='IF101', name='Programming', credits=3, semester=1)
        ay = AcademicYear.objects.create(year='2024/2025', start_date='2024-07-01', end_date='2025-06-30')
        semester = Semester.objects.create(academic_year=ay, name='Ganjil', code='20241', start_date='2024-07-01', end_date='2024-12-31')
        self.class_obj = Class.objects.create(course=course, semester=semester, name='A', code='IF101-A', lecturer=self.user)
        self.assignment = Assignment.objects.create(
            class_meta=self.class_obj,
            title='Test Assignment',
            description='Test description',
            due_date=timezone.now() + timedelta(days=7),
            created_by=self.user,
        )

    def test_assignment_creation(self):
        self.assertEqual(self.assignment.title, 'Test Assignment')
        self.assertTrue(self.assignment.is_published)
        self.assertEqual(self.assignment.max_score, 100)

    def test_assignment_str(self):
        self.assertEqual(str(self.assignment), 'Test Assignment')

    def test_is_past_due(self):
        past = Assignment.objects.create(
            class_meta=self.class_obj,
            title='Past Due',
            due_date=timezone.now() - timedelta(days=1),
            created_by=self.user,
        )
        self.assertTrue(past.is_past_due())
        self.assertFalse(self.assignment.is_past_due())


class AssignmentSubmissionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='dosen1', password='test1234', role='dosen')
        self.student = User.objects.create_user(username='student1', password='test1234', role='mahasiswa')
        faculty = Faculty.objects.create(name='FT', code='FT')
        sp = StudyProgram.objects.create(faculty=faculty, name='IF', code='IF', degree='s1')
        course = Course.objects.create(study_program=sp, code='IF101', name='Programming', credits=3, semester=1)
        ay = AcademicYear.objects.create(year='2024/2025', start_date='2024-07-01', end_date='2025-06-30')
        semester = Semester.objects.create(academic_year=ay, name='Ganjil', code='20241', start_date='2024-07-01', end_date='2024-12-31')
        self.class_obj = Class.objects.create(course=course, semester=semester, name='A', code='IF101-A', lecturer=self.user)
        self.assignment = Assignment.objects.create(
            class_meta=self.class_obj, title='Test', due_date=timezone.now() + timedelta(days=7),
            created_by=self.user,
        )
        self.submission = AssignmentSubmission.objects.create(
            assignment=self.assignment, student=self.student, status='submitted',
        )

    def test_submission_creation(self):
        self.assertEqual(self.submission.status, 'submitted')
        self.assertEqual(self.submission.attempt_number, 1)

    def test_submission_str(self):
        self.assertIn('student1', str(self.submission))

    def test_submission_unique_together(self):
        with self.assertRaises(Exception):
            AssignmentSubmission.objects.create(
                assignment=self.assignment, student=self.student, attempt_number=1,
            )


class ViewTests(TestCase):
    def setUp(self):
        self.dosen = User.objects.create_user(username='dosen1', password='test1234', role='dosen')
        self.student = User.objects.create_user(username='student1', password='test1234', role='mahasiswa')
        faculty = Faculty.objects.create(name='FT', code='FT')
        sp = StudyProgram.objects.create(faculty=faculty, name='IF', code='IF', degree='s1')
        course = Course.objects.create(study_program=sp, code='IF101', name='Programming', credits=3, semester=1)
        ay = AcademicYear.objects.create(year='2024/2025', start_date='2024-07-01', end_date='2025-06-30')
        semester = Semester.objects.create(academic_year=ay, name='Ganjil', code='20241', start_date='2024-07-01', end_date='2024-12-31')
        self.class_obj = Class.objects.create(course=course, semester=semester, name='A', code='IF101-A', lecturer=self.dosen)
        self.assignment = Assignment.objects.create(
            class_meta=self.class_obj, title='Test', due_date=timezone.now() + timedelta(days=7),
            created_by=self.dosen,
        )

    def test_assignment_list_public(self):
        response = self.client.get(reverse('assignments:assignment_list'))
        self.assertEqual(response.status_code, 200)

    def test_assignment_detail(self):
        response = self.client.get(reverse('assignments:assignment_detail', args=[self.assignment.pk]))
        self.assertEqual(response.status_code, 200)

    def test_assignment_create_requires_login(self):
        response = self.client.get(reverse('assignments:assignment_create'))
        self.assertNotEqual(response.status_code, 200)

    def test_assignment_create_dosen(self):
        self.client.login(username='dosen1', password='test1234')
        response = self.client.get(reverse('assignments:assignment_create'))
        self.assertEqual(response.status_code, 200)

    def test_assignment_submit_student(self):
        self.client.login(username='student1', password='test1234')
        response = self.client.get(reverse('assignments:assignment_submit', args=[self.assignment.pk]))
        self.assertEqual(response.status_code, 200)


class ServiceTests(TestCase):
    def setUp(self):
        from .services import AssignmentService, AssignmentSubmissionService
        self.assignment_service = AssignmentService()
        self.submission_service = AssignmentSubmissionService()
        self.dosen = User.objects.create_user(username='dosen1', password='test1234', role='dosen')
        self.student = User.objects.create_user(username='student1', password='test1234', role='mahasiswa')
        faculty = Faculty.objects.create(name='FT', code='FT')
        sp = StudyProgram.objects.create(faculty=faculty, name='IF', code='IF', degree='s1')
        course = Course.objects.create(study_program=sp, code='IF101', name='Programming', credits=3, semester=1)
        ay = AcademicYear.objects.create(year='2024/2025', start_date='2024-07-01', end_date='2025-06-30')
        semester = Semester.objects.create(academic_year=ay, name='Ganjil', code='20241', start_date='2024-07-01', end_date='2024-12-31')
        self.class_obj = Class.objects.create(course=course, semester=semester, name='A', code='IF101-A', lecturer=self.dosen)
        self.assignment = Assignment.objects.create(
            class_meta=self.class_obj, title='Test', due_date=timezone.now() + timedelta(days=7),
            created_by=self.dosen,
        )

    def test_assignment_service_create(self):
        result = self.assignment_service.create(
            class_meta=self.class_obj, title='New Assignment',
            due_date=timezone.now() + timedelta(days=7), created_by=self.dosen,
        )
        self.assertTrue(result['success'])
        self.assertEqual(result['data'].title, 'New Assignment')

    def test_assignment_service_delete(self):
        result = self.assignment_service.delete(self.assignment.id)
        self.assertTrue(result['success'])

    def test_submission_service_submit(self):
        result = self.submission_service.submit(
            student_id=self.student.id, assignment_id=self.assignment.id,
        )
        self.assertTrue(result['success'])
        self.assertEqual(result['data'].status, 'submitted')

    def test_submission_service_grade(self):
        sub = self.submission_service.submit(
            student_id=self.student.id, assignment_id=self.assignment.id,
        )['data']
        result = self.submission_service.grade(
            submission_id=sub.id, score=85.0, feedback='Good work!', graded_by_id=self.dosen.id,
        )
        self.assertTrue(result['success'])
        self.assertEqual(result['data'].status, 'graded')


class RepositoryTests(TestCase):
    def setUp(self):
        from .repositories import AssignmentRepository, AssignmentSubmissionRepository
        self.assignment_repo = AssignmentRepository()
        self.submission_repo = AssignmentSubmissionRepository()
        self.dosen = User.objects.create_user(username='dosen1', password='test1234', role='dosen')
        self.student = User.objects.create_user(username='student1', password='test1234', role='mahasiswa')
        faculty = Faculty.objects.create(name='FT', code='FT')
        sp = StudyProgram.objects.create(faculty=faculty, name='IF', code='IF', degree='s1')
        course = Course.objects.create(study_program=sp, code='IF101', name='Programming', credits=3, semester=1)
        ay = AcademicYear.objects.create(year='2024/2025', start_date='2024-07-01', end_date='2025-06-30')
        semester = Semester.objects.create(academic_year=ay, name='Ganjil', code='20241', start_date='2024-07-01', end_date='2024-12-31')
        self.class_obj = Class.objects.create(course=course, semester=semester, name='A', code='IF101-A', lecturer=self.dosen)
        self.assignment = Assignment.objects.create(
            class_meta=self.class_obj, title='Test', due_date=timezone.now() + timedelta(days=7),
            created_by=self.dosen,
        )

    def test_assignment_repo_create(self):
        a = self.assignment_repo.create(
            class_meta=self.class_obj, title='Repo Test',
            due_date=timezone.now() + timedelta(days=7), created_by=self.dosen,
        )
        self.assertIsNotNone(a)

    def test_assignment_repo_get_by_class(self):
        qs = self.assignment_repo.get_by_class(self.class_obj.id)
        self.assertEqual(qs.count(), 1)

    def test_submission_repo_create(self):
        s = self.submission_repo.create(assignment=self.assignment, student=self.student)
        self.assertIsNotNone(s)


class SerializerTests(TestCase):
    def setUp(self):
        from .serializers import AssignmentSerializer
        self.dosen = User.objects.create_user(username='dosen1', password='test1234', role='dosen')
        faculty = Faculty.objects.create(name='FT', code='FT')
        sp = StudyProgram.objects.create(faculty=faculty, name='IF', code='IF', degree='s1')
        course = Course.objects.create(study_program=sp, code='IF101', name='Programming', credits=3, semester=1)
        ay = AcademicYear.objects.create(year='2024/2025', start_date='2024-07-01', end_date='2025-06-30')
        semester = Semester.objects.create(academic_year=ay, name='Ganjil', code='20241', start_date='2024-07-01', end_date='2024-12-31')
        class_obj = Class.objects.create(course=course, semester=semester, name='A', code='IF101-A', lecturer=self.dosen)
        self.assignment = Assignment.objects.create(
            class_meta=class_obj, title='Test', due_date=timezone.now() + timedelta(days=7),
            created_by=self.dosen,
        )

    def test_assignment_serializer(self):
        from .serializers import AssignmentSerializer
        serializer = AssignmentSerializer(self.assignment)
        self.assertEqual(serializer.data['title'], 'Test')
        self.assertIn('submissions_count', serializer.data)
