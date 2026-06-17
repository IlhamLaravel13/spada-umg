from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Faculty, StudyProgram, AcademicYear, Semester, Course, Class, Enrollment

User = get_user_model()


class FacultyModelTest(TestCase):
    def setUp(self):
        self.faculty = Faculty.objects.create(
            name='Faculty of Engineering',
            code='FT',
            description='Engineering faculty'
        )

    def test_faculty_creation(self):
        self.assertEqual(self.faculty.name, 'Faculty of Engineering')
        self.assertEqual(self.faculty.code, 'FT')
        self.assertTrue(self.faculty.is_active)
        self.assertEqual(self.faculty.slug, 'faculty-of-engineering')

    def test_faculty_str(self):
        self.assertEqual(str(self.faculty), 'Faculty of Engineering')

    def test_faculty_ordering(self):
        f1 = Faculty.objects.create(name='A Faculty', code='AF')
        f2 = Faculty.objects.create(name='B Faculty', code='BF')
        faculties = Faculty.objects.all()
        self.assertEqual(faculties[0], f1)
        self.assertEqual(faculties[1], f2)


class StudyProgramModelTest(TestCase):
    def setUp(self):
        self.faculty = Faculty.objects.create(name='FT', code='FT')
        self.sp = StudyProgram.objects.create(
            faculty=self.faculty,
            name='Informatics',
            code='IF',
            degree='s1',
        )

    def test_study_program_creation(self):
        self.assertEqual(self.sp.name, 'Informatics')
        self.assertEqual(self.sp.degree, 's1')
        self.assertEqual(self.sp.faculty, self.faculty)

    def test_study_program_str(self):
        self.assertEqual(str(self.sp), 'Informatics (S1)')


class AcademicYearModelTest(TestCase):
    def setUp(self):
        self.ay = AcademicYear.objects.create(
            year='2024/2025',
            start_date='2024-07-01',
            end_date='2025-06-30',
        )

    def test_academic_year_creation(self):
        self.assertEqual(self.ay.year, '2024/2025')
        self.assertFalse(self.ay.is_active)

    def test_academic_year_str(self):
        self.assertEqual(str(self.ay), '2024/2025')


class SemesterModelTest(TestCase):
    def setUp(self):
        self.ay = AcademicYear.objects.create(
            year='2024/2025', start_date='2024-07-01', end_date='2025-06-30'
        )
        self.semester = Semester.objects.create(
            academic_year=self.ay,
            name='Ganjil',
            code='20241',
            start_date='2024-07-01',
            end_date='2024-12-31',
        )

    def test_semester_creation(self):
        self.assertEqual(self.semester.name, 'Ganjil')
        self.assertEqual(str(self.semester), '2024/2025 - Ganjil')


class CourseModelTest(TestCase):
    def setUp(self):
        faculty = Faculty.objects.create(name='FT', code='FT')
        self.sp = StudyProgram.objects.create(faculty=faculty, name='IF', code='IF', degree='s1')
        self.course = Course.objects.create(
            study_program=self.sp,
            code='IF101',
            name='Programming',
            credits=3,
            semester=1,
        )

    def test_course_creation(self):
        self.assertEqual(self.course.code, 'IF101')
        self.assertEqual(str(self.course), 'IF101 - Programming')
        self.assertEqual(self.course.slug, 'programming')


class ClassModelTest(TestCase):
    def setUp(self):
        faculty = Faculty.objects.create(name='FT', code='FT')
        sp = StudyProgram.objects.create(faculty=faculty, name='IF', code='IF', degree='s1')
        course = Course.objects.create(study_program=sp, code='IF101', name='Programming', credits=3, semester=1)
        ay = AcademicYear.objects.create(year='2024/2025', start_date='2024-07-01', end_date='2025-06-30')
        semester = Semester.objects.create(academic_year=ay, name='Ganjil', code='20241', start_date='2024-07-01', end_date='2024-12-31')
        self.class_obj = Class.objects.create(
            course=course, semester=semester, name='A', code='IF101-A', class_type='reguler', max_students=40,
        )

    def test_class_creation(self):
        self.assertEqual(self.class_obj.name, 'A')
        self.assertEqual(str(self.class_obj), 'IF101 - A (2024/2025 - Ganjil)')

    def test_class_defaults(self):
        self.assertEqual(self.class_obj.max_students, 40)
        self.assertEqual(self.class_obj.class_type, 'reguler')
        self.assertTrue(self.class_obj.is_active)


class EnrollmentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='student1', password='test1234', role='mahasiswa')
        faculty = Faculty.objects.create(name='FT', code='FT')
        sp = StudyProgram.objects.create(faculty=faculty, name='IF', code='IF', degree='s1')
        course = Course.objects.create(study_program=sp, code='IF101', name='Programming', credits=3, semester=1)
        ay = AcademicYear.objects.create(year='2024/2025', start_date='2024-07-01', end_date='2025-06-30')
        semester = Semester.objects.create(academic_year=ay, name='Ganjil', code='20241', start_date='2024-07-01', end_date='2024-12-31')
        self.class_obj = Class.objects.create(course=course, semester=semester, name='A', code='IF101-A')
        self.enrollment = Enrollment.objects.create(
            student=self.user, class_enrolled=self.class_obj, status='active',
        )

    def test_enrollment_creation(self):
        self.assertEqual(self.enrollment.status, 'active')
        self.assertEqual(str(self.enrollment), f'{self.user} - {self.class_obj}')

    def test_unique_enrollment(self):
        with self.assertRaises(Exception):
            Enrollment.objects.create(student=self.user, class_enrolled=self.class_obj)


class ViewTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username='admin', password='admin1234', email='admin@test.com')
        self.user = User.objects.create_user(username='user', password='test1234', role='mahasiswa')
        self.faculty = Faculty.objects.create(name='FT', code='FT')

    def test_faculty_list_public(self):
        response = self.client.get(reverse('academics:faculty_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'FT')

    def test_faculty_create_requires_login(self):
        response = self.client.get(reverse('academics:faculty_create'))
        self.assertNotEqual(response.status_code, 200)

    def test_faculty_create_admin(self):
        self.client.login(username='admin', password='admin1234')
        response = self.client.get(reverse('academics:faculty_create'))
        self.assertEqual(response.status_code, 200)

    def test_course_list(self):
        response = self.client.get(reverse('academics:course_list'))
        self.assertEqual(response.status_code, 200)

    def test_class_list(self):
        response = self.client.get(reverse('academics:class_list'))
        self.assertEqual(response.status_code, 200)

    def test_semester_list(self):
        response = self.client.get(reverse('academics:semester_list'))
        self.assertEqual(response.status_code, 200)

    def test_academic_year_list(self):
        response = self.client.get(reverse('academics:academic_year_list'))
        self.assertEqual(response.status_code, 200)

    def test_enrollment_list(self):
        response = self.client.get(reverse('academics:enrollment_list'))
        self.assertEqual(response.status_code, 200)


class ServiceTests(TestCase):
    def setUp(self):
        from .services import FacultyService, StudyProgramService, CourseService, ClassService
        from .services import EnrollmentService, SemesterService, AcademicYearService
        self.faculty_service = FacultyService()
        self.sp_service = StudyProgramService()
        self.course_service = CourseService()
        self.class_service = ClassService()
        self.enrollment_service = EnrollmentService()
        self.semester_service = SemesterService()
        self.ay_service = AcademicYearService()

        self.faculty = Faculty.objects.create(name='FT', code='FT')
        self.sp = StudyProgram.objects.create(faculty=self.faculty, name='IF', code='IF', degree='s1')
        self.course = Course.objects.create(study_program=self.sp, code='IF101', name='Programming', credits=3, semester=1)
        ay = AcademicYear.objects.create(year='2024/2025', start_date='2024-07-01', end_date='2025-06-30')
        self.semester = Semester.objects.create(academic_year=ay, name='Ganjil', code='20241', start_date='2024-07-01', end_date='2024-12-31')
        self.class_obj = Class.objects.create(course=self.course, semester=self.semester, name='A', code='IF101-A')
        self.student = User.objects.create_user(username='student', password='test1234', role='mahasiswa')

    def test_faculty_service_create(self):
        result = self.faculty_service.create(name='New Faculty', code='NF')
        self.assertTrue(result['success'])
        self.assertEqual(result['data'].name, 'New Faculty')

    def test_faculty_service_get_all(self):
        qs = self.faculty_service.get_all()
        self.assertEqual(qs.count(), 1)

    def test_sp_service_get_by_faculty(self):
        qs = self.sp_service.get_by_faculty(self.faculty.id)
        self.assertEqual(qs.count(), 1)

    def test_course_service_create(self):
        result = self.course_service.create(study_program=self.sp, code='IF102', name='Data Structures', credits=3, semester=2)
        self.assertTrue(result['success'])

    def test_enrollment_service_enroll(self):
        result = self.enrollment_service.enroll_student(self.student.id, self.class_obj.id)
        self.assertTrue(result['success'])
        self.assertEqual(result['data'].status, 'active')

    def test_enrollment_service_duplicate_enroll(self):
        self.enrollment_service.enroll_student(self.student.id, self.class_obj.id)
        result = self.enrollment_service.enroll_student(self.student.id, self.class_obj.id)
        self.assertFalse(result['success'])

    def test_enrollment_service_withdraw(self):
        enrollment = self.enrollment_service.enroll_student(self.student.id, self.class_obj.id)['data']
        result = self.enrollment_service.withdraw_student(enrollment.id)
        self.assertTrue(result['success'])

    def test_semester_activate(self):
        result = self.semester_service.activate(self.semester.id)
        self.assertTrue(result['success'])
        self.semester.refresh_from_db()
        self.assertTrue(self.semester.is_active)

    def test_ay_service_create(self):
        result = self.ay_service.create(year='2025/2026', start_date='2025-07-01', end_date='2026-06-30')
        self.assertTrue(result['success'])


class RepositoryTests(TestCase):
    def setUp(self):
        from .repositories import FacultyRepository, StudyProgramRepository
        from .repositories import CourseRepository, ClassRepository, EnrollmentRepository
        self.faculty_repo = FacultyRepository()
        self.sp_repo = StudyProgramRepository()
        self.course_repo = CourseRepository()
        self.class_repo = ClassRepository()
        self.enrollment_repo = EnrollmentRepository()

        faculty = Faculty.objects.create(name='FT', code='FT')
        sp = StudyProgram.objects.create(faculty=faculty, name='IF', code='IF', degree='s1')
        self.course = Course.objects.create(study_program=sp, code='IF101', name='Programming', credits=3, semester=1)

    def test_faculty_get_active(self):
        qs = self.faculty_repo.get_active()
        self.assertEqual(qs.count(), 1)

    def test_faculty_get_by_code(self):
        f = self.faculty_repo.get_by_code('FT')
        self.assertIsNotNone(f)
        self.assertEqual(f.name, 'FT')

    def test_sp_search(self):
        qs = self.sp_repo.search('IF')
        self.assertEqual(qs.count(), 1)

    def test_course_get_by_study_program(self):
        qs = self.course_repo.get_by_study_program(1)
        self.assertEqual(qs.count(), 1)

    def test_faculty_create_and_delete(self):
        f = self.faculty_repo.create(name='Test', code='TST')
        self.assertIsNotNone(f)
        deleted = self.faculty_repo.delete(f.id)
        self.assertTrue(deleted)


class SerializerTests(TestCase):
    def setUp(self):
        from .serializers import FacultySerializer, StudyProgramSerializer, CourseSerializer
        faculty = Faculty.objects.create(name='FT', code='FT')
        sp = StudyProgram.objects.create(faculty=faculty, name='IF', code='IF', degree='s1')
        self.course = Course.objects.create(study_program=sp, code='IF101', name='Programming', credits=3, semester=1)

    def test_faculty_serializer(self):
        from .serializers import FacultySerializer
        faculty = Faculty.objects.first()
        serializer = FacultySerializer(faculty)
        self.assertEqual(serializer.data['code'], 'FT')
        self.assertIn('study_programs_count', serializer.data)

    def test_course_serializer(self):
        from .serializers import CourseSerializer
        serializer = CourseSerializer(self.course)
        self.assertEqual(serializer.data['code'], 'IF101')
        self.assertIn('study_program_name', serializer.data)
