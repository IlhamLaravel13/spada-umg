from django.db.models import QuerySet, Q
from django.utils import timezone
from .models import AttendanceSession, Attendance


class AttendanceSessionRepository:
    def get_all(self) -> QuerySet[AttendanceSession]:
        return AttendanceSession.objects.select_related('class_meta__course', 'created_by').all()

    def get_active(self) -> QuerySet[AttendanceSession]:
        return AttendanceSession.objects.filter(is_active=True)

    def get_by_id(self, session_id: int) -> AttendanceSession | None:
        return AttendanceSession.objects.filter(id=session_id).first()

    def get_by_class(self, class_id: int) -> QuerySet[AttendanceSession]:
        return AttendanceSession.objects.filter(class_meta_id=class_id)

    def get_today_sessions(self, class_id: int = None) -> QuerySet[AttendanceSession]:
        qs = AttendanceSession.objects.filter(date=timezone.now().date(), is_active=True)
        if class_id:
            qs = qs.filter(class_meta_id=class_id)
        return qs

    def get_active_by_class_today(self, class_id: int) -> AttendanceSession | None:
        return AttendanceSession.objects.filter(
            class_meta_id=class_id,
            date=timezone.now().date(),
            is_active=True,
        ).first()

    def search(self, query: str) -> QuerySet[AttendanceSession]:
        return AttendanceSession.objects.filter(
            Q(title__icontains=query) | Q(topic__icontains=query) |
            Q(class_meta__course__name__icontains=query) | Q(class_meta__code__icontains=query)
        )

    def create(self, **kwargs) -> AttendanceSession:
        return AttendanceSession.objects.create(**kwargs)

    def update(self, session_id: int, **kwargs) -> AttendanceSession | None:
        updated = AttendanceSession.objects.filter(id=session_id).update(**kwargs)
        if updated:
            return self.get_by_id(session_id)
        return None

    def delete(self, session_id: int) -> bool:
        return AttendanceSession.objects.filter(id=session_id).delete()[0] > 0

    def count(self) -> int:
        return AttendanceSession.objects.count()


class AttendanceRepository:
    def get_all(self) -> QuerySet[Attendance]:
        return Attendance.objects.select_related('session__class_meta', 'student').all()

    def get_by_id(self, attendance_id: int) -> Attendance | None:
        return Attendance.objects.filter(id=attendance_id).first()

    def get_by_session(self, session_id: int) -> QuerySet[Attendance]:
        return Attendance.objects.filter(session_id=session_id).select_related('student')

    def get_by_student(self, student_id: int) -> QuerySet[Attendance]:
        return Attendance.objects.filter(student_id=student_id).select_related('session__class_meta')

    def get_by_student_and_class(self, student_id: int, class_id: int) -> QuerySet[Attendance]:
        return Attendance.objects.filter(
            student_id=student_id,
            session__class_meta_id=class_id,
        ).select_related('session')

    def get_existing(self, session_id: int, student_id: int) -> Attendance | None:
        return Attendance.objects.filter(session_id=session_id, student_id=student_id).first()

    def create(self, **kwargs) -> Attendance:
        return Attendance.objects.create(**kwargs)

    def update(self, attendance_id: int, **kwargs) -> Attendance | None:
        updated = Attendance.objects.filter(id=attendance_id).update(**kwargs)
        if updated:
            return self.get_by_id(attendance_id)
        return None

    def delete(self, attendance_id: int) -> bool:
        return Attendance.objects.filter(id=attendance_id).delete()[0] > 0

    def count_by_session(self, session_id: int) -> int:
        return Attendance.objects.filter(session_id=session_id).count()

    def count_present_by_session(self, session_id: int) -> int:
        return Attendance.objects.filter(session_id=session_id, status='present').count()

    def get_report(self, class_id: int, start_date=None, end_date=None) -> QuerySet[Attendance]:
        qs = Attendance.objects.filter(session__class_meta_id=class_id)
        if start_date:
            qs = qs.filter(session__date__gte=start_date)
        if end_date:
            qs = qs.filter(session__date__lte=end_date)
        return qs.select_related('student', 'session')
