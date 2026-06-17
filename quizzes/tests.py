from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models import Quiz, QuizQuestion, QuizAnswer, QuizAttempt, QuizResponse
from academics.models import Faculty, StudyProgram, AcademicYear, Semester, Course, Class

User = get_user_model()


class QuizModelTest(TestCase):
    def setUp(self):
        self.dosen = User.objects.create_user(username='dosen1', password='test1234', role='dosen')
        faculty = Faculty.objects.create(name='FT', code='FT')
        sp = StudyProgram.objects.create(faculty=faculty, name='IF', code='IF', degree='s1')
        course = Course.objects.create(study_program=sp, code='IF101', name='Programming', credits=3, semester=1)
        ay = AcademicYear.objects.create(year='2024/2025', start_date='2024-07-01', end_date='2025-06-30')
        semester = Semester.objects.create(academic_year=ay, name='Ganjil', code='20241', start_date='2024-07-01', end_date='2024-12-31')
        self.class_obj = Class.objects.create(course=course, semester=semester, name='A', code='IF101-A', lecturer=self.dosen)
        self.quiz = Quiz.objects.create(
            class_meta=self.class_obj, title='Test Quiz',
            due_date=timezone.now() + timedelta(days=7), created_by=self.dosen,
        )

    def test_quiz_creation(self):
        self.assertEqual(self.quiz.title, 'Test Quiz')
        self.assertEqual(self.quiz.time_limit_minutes, 30)
        self.assertFalse(self.quiz.is_published)

    def test_quiz_str(self):
        self.assertEqual(str(self.quiz), 'Test Quiz')


class QuizQuestionModelTest(TestCase):
    def setUp(self):
        self.dosen = User.objects.create_user(username='dosen1', password='test1234', role='dosen')
        faculty = Faculty.objects.create(name='FT', code='FT')
        sp = StudyProgram.objects.create(faculty=faculty, name='IF', code='IF', degree='s1')
        course = Course.objects.create(study_program=sp, code='IF101', name='Programming', credits=3, semester=1)
        ay = AcademicYear.objects.create(year='2024/2025', start_date='2024-07-01', end_date='2025-06-30')
        semester = Semester.objects.create(academic_year=ay, name='Ganjil', code='20241', start_date='2024-07-01', end_date='2024-12-31')
        class_obj = Class.objects.create(course=course, semester=semester, name='A', code='IF101-A', lecturer=self.dosen)
        self.quiz = Quiz.objects.create(class_meta=class_obj, title='Test', due_date=timezone.now() + timedelta(days=7), created_by=self.dosen)
        self.question = QuizQuestion.objects.create(quiz=self.quiz, question_text='What is 2+2?', question_type='multiple_choice', points=10, order=1)
        self.answer = QuizAnswer.objects.create(question=self.question, answer_text='4', is_correct=True)

    def test_question_creation(self):
        self.assertEqual(self.question.question_text, 'What is 2+2?')
        self.assertEqual(self.question.points, 10)

    def test_answer_creation(self):
        self.assertTrue(self.answer.is_correct)
        self.assertEqual(self.answer.answer_text, '4')


class QuizAttemptModelTest(TestCase):
    def setUp(self):
        self.dosen = User.objects.create_user(username='dosen1', password='test1234', role='dosen')
        self.student = User.objects.create_user(username='student1', password='test1234', role='mahasiswa')
        faculty = Faculty.objects.create(name='FT', code='FT')
        sp = StudyProgram.objects.create(faculty=faculty, name='IF', code='IF', degree='s1')
        course = Course.objects.create(study_program=sp, code='IF101', name='Programming', credits=3, semester=1)
        ay = AcademicYear.objects.create(year='2024/2025', start_date='2024-07-01', end_date='2025-06-30')
        semester = Semester.objects.create(academic_year=ay, name='Ganjil', code='20241', start_date='2024-07-01', end_date='2024-12-31')
        class_obj = Class.objects.create(course=course, semester=semester, name='A', code='IF101-A', lecturer=self.dosen)
        self.quiz = Quiz.objects.create(class_meta=class_obj, title='Test', due_date=timezone.now() + timedelta(days=7), created_by=self.dosen)
        self.attempt = QuizAttempt.objects.create(quiz=self.quiz, student=self.student)

    def test_attempt_creation(self):
        self.assertIsNotNone(self.attempt)
        self.assertFalse(self.attempt.is_completed())

    def test_attempt_str(self):
        self.assertIn('student1', str(self.attempt))


class ViewTests(TestCase):
    def setUp(self):
        self.dosen = User.objects.create_user(username='dosen1', password='test1234', role='dosen')
        self.student = User.objects.create_user(username='student1', password='test1234', role='mahasiswa')
        faculty = Faculty.objects.create(name='FT', code='FT')
        sp = StudyProgram.objects.create(faculty=faculty, name='IF', code='IF', degree='s1')
        course = Course.objects.create(study_program=sp, code='IF101', name='Programming', credits=3, semester=1)
        ay = AcademicYear.objects.create(year='2024/2025', start_date='2024-07-01', end_date='2025-06-30')
        semester = Semester.objects.create(academic_year=ay, name='Ganjil', code='20241', start_date='2024-07-01', end_date='2024-12-31')
        class_obj = Class.objects.create(course=course, semester=semester, name='A', code='IF101-A', lecturer=self.dosen)
        self.quiz = Quiz.objects.create(class_meta=class_obj, title='Test', due_date=timezone.now() + timedelta(days=7), created_by=self.dosen)

    def test_quiz_list_public(self):
        response = self.client.get(reverse('quizzes:quiz_list'))
        self.assertEqual(response.status_code, 200)

    def test_quiz_detail(self):
        response = self.client.get(reverse('quizzes:quiz_detail', args=[self.quiz.pk]))
        self.assertEqual(response.status_code, 200)

    def test_quiz_create_requires_login(self):
        response = self.client.get(reverse('quizzes:quiz_create'))
        self.assertNotEqual(response.status_code, 200)

    def test_quiz_create_dosen(self):
        self.client.login(username='dosen1', password='test1234')
        response = self.client.get(reverse('quizzes:quiz_create'))
        self.assertEqual(response.status_code, 200)


class ServiceTests(TestCase):
    def setUp(self):
        from .services import QuizService, QuizAttemptService, QuizQuestionService
        self.quiz_service = QuizService()
        self.attempt_service = QuizAttemptService()
        self.question_service = QuizQuestionService()
        self.dosen = User.objects.create_user(username='dosen1', password='test1234', role='dosen')
        self.student = User.objects.create_user(username='student1', password='test1234', role='mahasiswa')
        faculty = Faculty.objects.create(name='FT', code='FT')
        sp = StudyProgram.objects.create(faculty=faculty, name='IF', code='IF', degree='s1')
        course = Course.objects.create(study_program=sp, code='IF101', name='Programming', credits=3, semester=1)
        ay = AcademicYear.objects.create(year='2024/2025', start_date='2024-07-01', end_date='2025-06-30')
        semester = Semester.objects.create(academic_year=ay, name='Ganjil', code='20241', start_date='2024-07-01', end_date='2024-12-31')
        class_obj = Class.objects.create(course=course, semester=semester, name='A', code='IF101-A', lecturer=self.dosen)
        self.quiz = Quiz.objects.create(class_meta=class_obj, title='Test', due_date=timezone.now() + timedelta(days=7), created_by=self.dosen)

    def test_quiz_service_create(self):
        faculty = Faculty.objects.first()
        sp = StudyProgram.objects.first()
        course = Course.objects.first()
        ay = AcademicYear.objects.first()
        semester = Semester.objects.first()
        class_obj = Class.objects.first()
        result = self.quiz_service.create(
            class_meta=class_obj, title='New Quiz',
            due_date=timezone.now() + timedelta(days=7), created_by=self.dosen,
        )
        self.assertTrue(result['success'])
        self.assertEqual(result['data'].title, 'New Quiz')

    def test_quiz_service_delete(self):
        result = self.quiz_service.delete(self.quiz.id)
        self.assertTrue(result['success'])

    def test_attempt_start(self):
        result = self.attempt_service.start_attempt(self.student.id, self.quiz.id)
        self.assertTrue(result['success'])

    def test_attempt_submit_answer(self):
        attempt = self.attempt_service.start_attempt(self.student.id, self.quiz.id)['data']
        question = QuizQuestion.objects.create(quiz=self.quiz, question_text='Q1', question_type='multiple_choice', points=10, order=1)
        answer = QuizAnswer.objects.create(question=question, answer_text='A1', is_correct=True)
        result = self.attempt_service.submit_answer(attempt.id, question.id, selected_answer_id=answer.id)
        self.assertTrue(result['success'])


class RepositoryTests(TestCase):
    def setUp(self):
        from .repositories import QuizRepository, QuizQuestionRepository, QuizAttemptRepository
        self.quiz_repo = QuizRepository()
        self.question_repo = QuizQuestionRepository()
        self.attempt_repo = QuizAttemptRepository()
        self.dosen = User.objects.create_user(username='dosen1', password='test1234', role='dosen')
        faculty = Faculty.objects.create(name='FT', code='FT')
        sp = StudyProgram.objects.create(faculty=faculty, name='IF', code='IF', degree='s1')
        course = Course.objects.create(study_program=sp, code='IF101', name='Programming', credits=3, semester=1)
        ay = AcademicYear.objects.create(year='2024/2025', start_date='2024-07-01', end_date='2025-06-30')
        semester = Semester.objects.create(academic_year=ay, name='Ganjil', code='20241', start_date='2024-07-01', end_date='2024-12-31')
        class_obj = Class.objects.create(course=course, semester=semester, name='A', code='IF101-A', lecturer=self.dosen)
        self.quiz = Quiz.objects.create(class_meta=class_obj, title='Test', due_date=timezone.now() + timedelta(days=7), created_by=self.dosen)

    def test_quiz_repo_create(self):
        faculty = Faculty.objects.first()
        sp = StudyProgram.objects.first()
        course = Course.objects.first()
        ay = AcademicYear.objects.first()
        semester = Semester.objects.first()
        class_obj = Class.objects.first()
        q = self.quiz_repo.create(class_meta=class_obj, title='Repo Quiz', due_date=timezone.now() + timedelta(days=7), created_by=self.dosen)
        self.assertIsNotNone(q)

    def test_quiz_repo_get_by_class(self):
        qs = self.quiz_repo.get_by_class(1)
        self.assertEqual(qs.count(), 1)


class SerializerTests(TestCase):
    def setUp(self):
        from .serializers import QuizSerializer
        self.dosen = User.objects.create_user(username='dosen1', password='test1234', role='dosen')
        faculty = Faculty.objects.create(name='FT', code='FT')
        sp = StudyProgram.objects.create(faculty=faculty, name='IF', code='IF', degree='s1')
        course = Course.objects.create(study_program=sp, code='IF101', name='Programming', credits=3, semester=1)
        ay = AcademicYear.objects.create(year='2024/2025', start_date='2024-07-01', end_date='2025-06-30')
        semester = Semester.objects.create(academic_year=ay, name='Ganjil', code='20241', start_date='2024-07-01', end_date='2024-12-31')
        class_obj = Class.objects.create(course=course, semester=semester, name='A', code='IF101-A', lecturer=self.dosen)
        self.quiz = Quiz.objects.create(class_meta=class_obj, title='Test', due_date=timezone.now() + timedelta(days=7), created_by=self.dosen)

    def test_quiz_serializer(self):
        from .serializers import QuizSerializer
        serializer = QuizSerializer(self.quiz)
        self.assertEqual(serializer.data['title'], 'Test')
        self.assertIn('question_count', serializer.data)
