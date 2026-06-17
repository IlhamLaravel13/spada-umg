from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import AttendanceSession, Attendance
from academics.models import Faculty, StudyProgram, AcademicYear, Semester, Course, Class as ClassModel, Enrollment

User = get_user_model()


class BaseAttendanceTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.dosen = User.objects.create_user(
            username='dosen1', password='test123', role='dosen',
            first_name='Dosen', last_name='Satu',
        )
        self.mahasiswa = User.objects.create_user(
            username='mhs1', password='test123', role='mahasiswa',
            first_name='Mhs', last_name='Satu', nim='2024001',
        )
        self.admin = User.objects.create_user(
            username='admin1', password='test123', role='admin',
            first_name='Admin', last_name='Satu',
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
        Enrollment.objects.create(student=self.mahasiswa, class_enrolled=self.class_obj, status='active')

    def _create_session(self, **kwargs):
        data = {
            'class_meta': self.class_obj,
            'title': 'Pertemuan 1',
            'date': timezone.now().date(),
            'start_time': timezone.now().time().replace(hour=8, minute=0, second=0),
            'end_time': timezone.now().time().replace(hour=10, minute=0, second=0),
            'topic': 'Pengantar',
            'meeting_number': 1,
            'created_by': self.dosen,
            'is_active': True,
            'qr_code_secret': 'test-secret-123',
        }
        data.update(kwargs)
        return AttendanceSession.objects.create(**data)


class AttendanceSessionModelTest(BaseAttendanceTest):
    def test_create_session(self):
        session = self._create_session()
        self.assertEqual(session.title, 'Pertemuan 1')
        self.assertEqual(session.class_meta, self.class_obj)
        self.assertTrue(session.is_active)
        self.assertEqual(str(session), f"{self.class_obj} - {timezone.now().date()}")

    def test_session_ordering(self):
        s1 = self._create_session(title='Sesi 1', date='2024-10-01')
        s2 = self._create_session(title='Sesi 2', date='2024-10-02')
        qs = AttendanceSession.objects.all()
        self.assertEqual(qs.first(), s2)


class AttendanceModelTest(BaseAttendanceTest):
    def test_create_attendance(self):
        session = self._create_session()
        attendance = Attendance.objects.create(
            session=session, student=self.mahasiswa, status='present',
        )
        self.assertEqual(attendance.status, 'present')
        self.assertEqual(str(attendance), f"{self.mahasiswa} - {session} - Hadir")

    def test_unique_together(self):
        session = self._create_session()
        Attendance.objects.create(session=session, student=self.mahasiswa)
        with self.assertRaises(Exception):
            Attendance.objects.create(session=session, student=self.mahasiswa)


class AttendanceViewsTest(BaseAttendanceTest):
    def test_session_list_requires_login(self):
        response = self.client.get(reverse('attendance:session_list'))
        self.assertNotEqual(response.status_code, 200)

    def test_session_list_dosen(self):
        self.client.login(username='dosen1', password='test123')
        response = self.client.get(reverse('attendance:session_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'attendance/session_list.html')

    def test_session_create(self):
        self.client.login(username='dosen1', password='test123')
        response = self.client.post(reverse('attendance:session_create'), {
            'class_meta': self.class_obj.id,
            'title': 'Pertemuan Baru',
            'date': '2024-10-15',
            'start_time': '08:00',
            'end_time': '10:00',
            'topic': 'Testing',
            'meeting_number': 2,
            'is_active': True,
        })
        self.assertIn(response.status_code, [200, 302])

    def test_take_attendance(self):
        self.client.login(username='mhs1', password='test123')
        session = self._create_session()
        response = self.client.get(reverse('attendance:take_attendance', args=[session.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'attendance/attendance_take.html')

    def test_check_in(self):
        self.client.login(username='mhs1', password='test123')
        session = self._create_session()
        response = self.client.post(reverse('attendance:take_attendance', args=[session.id]), {
            'qr_secret': 'test-secret-123',
        })
        self.assertIn(response.status_code, [200, 302])

    def test_my_attendance(self):
        self.client.login(username='mhs1', password='test123')
        response = self.client.get(reverse('attendance:my_attendance'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'attendance/my_attendance.html')

    def test_attendance_report(self):
        self.client.login(username='dosen1', password='test123')
        response = self.client.get(reverse('attendance:attendance_report'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'attendance/attendance_report.html')


class AttendanceServiceTest(BaseAttendanceTest):
    def test_check_in_success(self):
        from .services import AttendanceService
        service = AttendanceService()
        session = self._create_session()
        result = service.check_in(self.mahasiswa, session.id)
        self.assertTrue(result['success'])

    def test_check_in_duplicate(self):
        from .services import AttendanceService
        service = AttendanceService()
        session = self._create_session()
        service.check_in(self.mahasiswa, session.id)
        result = service.check_in(self.mahasiswa, session.id)
        self.assertFalse(result['success'])

    def test_check_in_not_enrolled(self):
        from .services import AttendanceService
        service = AttendanceService()
        other = User.objects.create_user(username='other', password='test123', role='mahasiswa')
        session = self._create_session()
        result = service.check_in(other, session.id)
        self.assertFalse(result['success'])

    def test_generate_report(self):
        from .services import AttendanceService
        service = AttendanceService()
        session = self._create_session()
        service.check_in(self.mahasiswa, session.id)
        result = service.generate_report(self.class_obj.id)
        self.assertTrue(result['success'])
        self.assertEqual(len(result['data']['reports']), 1)
