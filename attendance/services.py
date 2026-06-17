import io
import uuid
import hashlib
import logging
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from django.core.files.base import ContentFile
from django.conf import settings

from .repositories import AttendanceSessionRepository, AttendanceRepository
from academics.repositories import ClassRepository, EnrollmentRepository

logger = logging.getLogger(__name__)


class AttendanceService:
    def __init__(self):
        self.session_repo = AttendanceSessionRepository()
        self.attendance_repo = AttendanceRepository()
        self.class_repo = ClassRepository()
        self.enrollment_repo = EnrollmentRepository()

    def get_all_sessions(self):
        return self.session_repo.get_all()

    def get_session_by_id(self, session_id: int):
        return self.session_repo.get_by_id(session_id)

    def get_sessions_by_class(self, class_id: int):
        return self.session_repo.get_by_class(class_id)

    def get_active_session_for_class(self, class_id: int):
        return self.session_repo.get_active_by_class_today(class_id)

    def create_session(self, **kwargs) -> dict:
        try:
            qr_secret = hashlib.sha256(
                f"{kwargs.get('class_meta_id')}-{kwargs.get('date')}-{uuid.uuid4().hex}".encode()
            ).hexdigest()[:50]
            kwargs['qr_code_secret'] = qr_secret
            session = self.session_repo.create(**kwargs)
            self._generate_qr_code(session)
            return {'success': True, 'data': session}
        except Exception as e:
            logger.exception("Failed to create attendance session")
            return {'success': False, 'error': str(e)}

    def update_session(self, session_id: int, **kwargs) -> dict:
        try:
            session = self.session_repo.update(session_id, **kwargs)
            if session:
                return {'success': True, 'data': session}
            return {'success': False, 'error': 'Session not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def delete_session(self, session_id: int) -> dict:
        try:
            if self.session_repo.delete(session_id):
                return {'success': True, 'message': 'Session deleted successfully'}
            return {'success': False, 'error': 'Session not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _generate_qr_code(self, session) -> None:
        try:
            import qrcode
            from qrcode.image.pil import PilImage

            qr_data = f"{session.id}:{session.qr_code_secret}"
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            filename = f'attendance/qrcodes/session_{session.id}.png'
            session.qr_code.save(filename, ContentFile(buffer.getvalue()), save=True)
        except ImportError:
            logger.warning("qrcode library not available, skipping QR generation")
        except Exception as e:
            logger.error(f"Failed to generate QR code: {e}")

    def check_in(self, user, session_id: int, **kwargs) -> dict:
        try:
            session = self.session_repo.get_by_id(session_id)
            if not session:
                return {'success': False, 'error': 'Sesi absensi tidak ditemukan'}
            if not session.is_active:
                return {'success': False, 'error': 'Sesi absensi sudah tidak aktif'}
            if session.date != timezone.now().date():
                return {'success': False, 'error': 'Sesi absensi bukan untuk hari ini'}

            now = timezone.localtime(timezone.now()).time()
            if now < session.start_time:
                return {'success': False, 'error': 'Sesi absensi belum dimulai'}
            if now > session.end_time:
                return {'success': False, 'error': 'Sesi absensi sudah berakhir'}

            enrolled = self.enrollment_repo.get_enrollment(user.id, session.class_meta_id)
            if not enrolled or enrolled.status != 'active':
                return {'success': False, 'error': 'Anda tidak terdaftar di kelas ini'}

            existing = self.attendance_repo.get_existing(session_id, user.id)
            if existing:
                return {'success': False, 'error': 'Anda sudah melakukan absensi untuk sesi ini'}

            is_late = now > session.start_time + timedelta(minutes=15)
            status = 'late' if is_late else 'present'

            attendance = self.attendance_repo.create(
                session=session,
                student=user,
                status=status,
                latitude=kwargs.get('latitude'),
                longitude=kwargs.get('longitude'),
                notes=kwargs.get('notes', ''),
            )
            return {'success': True, 'data': attendance}
        except Exception as e:
            logger.exception("Check-in failed")
            return {'success': False, 'error': str(e)}

    def manual_check_in(self, user, session_id: int, student_id: int, **kwargs) -> dict:
        try:
            session = self.session_repo.get_by_id(session_id)
            if not session:
                return {'success': False, 'error': 'Session not found'}

            existing = self.attendance_repo.get_existing(session_id, student_id)
            if existing:
                return {'success': False, 'error': 'Student already checked in'}

            attendance = self.attendance_repo.create(
                session=session,
                student_id=student_id,
                status=kwargs.get('status', 'present'),
                notes=kwargs.get('notes', ''),
                verified_by=user,
            )
            return {'success': True, 'data': attendance}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def update_attendance_status(self, attendance_id: int, status: str, verified_by) -> dict:
        try:
            attendance = self.attendance_repo.update(
                attendance_id, status=status, verified_by=verified_by
            )
            if attendance:
                return {'success': True, 'data': attendance}
            return {'success': False, 'error': 'Attendance not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_attendances_for_session(self, session_id: int):
        return self.attendance_repo.get_by_session(session_id)

    def get_my_attendances(self, user):
        return self.attendance_repo.get_by_student(user.id)

    def get_student_attendances_for_class(self, student_id: int, class_id: int):
        return self.attendance_repo.get_by_student_and_class(student_id, class_id)

    def generate_report(self, class_id: int, start_date=None, end_date=None) -> dict:
        try:
            class_obj = self.class_repo.get_by_id(class_id)
            if not class_obj:
                return {'success': False, 'error': 'Class not found'}

            sessions = self.session_repo.get_by_class(class_id)
            if start_date:
                sessions = sessions.filter(date__gte=start_date)
            if end_date:
                sessions = sessions.filter(date__lte=end_date)

            enrollments = self.enrollment_repo.get_by_class(class_id).filter(status='active')

            report_data = []
            for enrollment in enrollments:
                student = enrollment.student
                student_data = {
                    'student': student,
                    'total_sessions': sessions.count(),
                    'present': 0,
                    'late': 0,
                    'absent': 0,
                    'excused': 0,
                    'sick': 0,
                    'percentage': 0.0,
                    'attendances': [],
                }

                for session in sessions:
                    att = self.attendance_repo.get_existing(session.id, student.id)
                    if att:
                        key = att.status
                        student_data[key] += 1
                        student_data['attendances'].append(att)
                    else:
                        student_data['absent'] += 1

                total = student_data['total_sessions']
                student_data['percentage'] = round(
                    ((student_data['present'] + student_data['late']) / total * 100) if total > 0 else 0, 1
                )
                report_data.append(student_data)

            return {
                'success': True,
                'data': {
                    'class': class_obj,
                    'sessions': sessions,
                    'reports': report_data,
                    'total_students': len(report_data),
                },
            }
        except Exception as e:
            logger.exception("Report generation failed")
            return {'success': False, 'error': str(e)}
