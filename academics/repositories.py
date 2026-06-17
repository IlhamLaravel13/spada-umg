from django.db.models import QuerySet, Q
from django.utils import timezone
from .models import Faculty, StudyProgram, AcademicYear, Semester, Course, Class, Enrollment


class FacultyRepository:
    def get_all(self) -> QuerySet[Faculty]:
        return Faculty.objects.all()

    def get_active(self) -> QuerySet[Faculty]:
        return Faculty.objects.filter(is_active=True)

    def get_by_id(self, faculty_id: int) -> Faculty | None:
        return Faculty.objects.filter(id=faculty_id).first()

    def get_by_slug(self, slug: str) -> Faculty | None:
        return Faculty.objects.filter(slug=slug).first()

    def get_by_code(self, code: str) -> Faculty | None:
        return Faculty.objects.filter(code=code).first()

    def search(self, query: str) -> QuerySet[Faculty]:
        return Faculty.objects.filter(
            Q(name__icontains=query) | Q(code__icontains=query) | Q(description__icontains=query)
        )

    def create(self, **kwargs) -> Faculty:
        return Faculty.objects.create(**kwargs)

    def update(self, faculty_id: int, **kwargs) -> Faculty | None:
        updated = Faculty.objects.filter(id=faculty_id).update(**kwargs)
        if updated:
            return self.get_by_id(faculty_id)
        return None

    def delete(self, faculty_id: int) -> bool:
        return Faculty.objects.filter(id=faculty_id).delete()[0] > 0

    def count(self) -> int:
        return Faculty.objects.count()


class StudyProgramRepository:
    def get_all(self) -> QuerySet[StudyProgram]:
        return StudyProgram.objects.select_related('faculty').all()

    def get_active(self) -> QuerySet[StudyProgram]:
        return StudyProgram.objects.filter(is_active=True)

    def get_by_id(self, sp_id: int) -> StudyProgram | None:
        return StudyProgram.objects.filter(id=sp_id).first()

    def get_by_faculty(self, faculty_id: int) -> QuerySet[StudyProgram]:
        return StudyProgram.objects.filter(faculty_id=faculty_id)

    def get_by_code(self, code: str) -> StudyProgram | None:
        return StudyProgram.objects.filter(code=code).first()

    def search(self, query: str) -> QuerySet[StudyProgram]:
        return StudyProgram.objects.filter(
            Q(name__icontains=query) | Q(code__icontains=query) | Q(description__icontains=query)
        )

    def create(self, **kwargs) -> StudyProgram:
        return StudyProgram.objects.create(**kwargs)

    def update(self, sp_id: int, **kwargs) -> StudyProgram | None:
        updated = StudyProgram.objects.filter(id=sp_id).update(**kwargs)
        if updated:
            return self.get_by_id(sp_id)
        return None

    def delete(self, sp_id: int) -> bool:
        return StudyProgram.objects.filter(id=sp_id).delete()[0] > 0


class AcademicYearRepository:
    def get_all(self) -> QuerySet[AcademicYear]:
        return AcademicYear.objects.all()

    def get_active(self) -> AcademicYear | None:
        return AcademicYear.objects.filter(is_active=True).first()

    def get_by_id(self, ay_id: int) -> AcademicYear | None:
        return AcademicYear.objects.filter(id=ay_id).first()

    def get_by_year(self, year: str) -> AcademicYear | None:
        return AcademicYear.objects.filter(year=year).first()

    def search(self, query: str) -> QuerySet[AcademicYear]:
        return AcademicYear.objects.filter(year__icontains=query)

    def create(self, **kwargs) -> AcademicYear:
        return AcademicYear.objects.create(**kwargs)

    def update(self, ay_id: int, **kwargs) -> AcademicYear | None:
        updated = AcademicYear.objects.filter(id=ay_id).update(**kwargs)
        if updated:
            return self.get_by_id(ay_id)
        return None

    def delete(self, ay_id: int) -> bool:
        return AcademicYear.objects.filter(id=ay_id).delete()[0] > 0

    def deactivate_all(self) -> int:
        return AcademicYear.objects.filter(is_active=True).update(is_active=False)


class SemesterRepository:
    def get_all(self) -> QuerySet[Semester]:
        return Semester.objects.select_related('academic_year').all()

    def get_active(self) -> Semester | None:
        return Semester.objects.filter(is_active=True).first()

    def get_by_id(self, semester_id: int) -> Semester | None:
        return Semester.objects.filter(id=semester_id).first()

    def get_by_academic_year(self, academic_year_id: int) -> QuerySet[Semester]:
        return Semester.objects.filter(academic_year_id=academic_year_id)

    def create(self, **kwargs) -> Semester:
        return Semester.objects.create(**kwargs)

    def update(self, semester_id: int, **kwargs) -> Semester | None:
        updated = Semester.objects.filter(id=semester_id).update(**kwargs)
        if updated:
            return self.get_by_id(semester_id)
        return None

    def delete(self, semester_id: int) -> bool:
        return Semester.objects.filter(id=semester_id).delete()[0] > 0

    def deactivate_all(self) -> int:
        return Semester.objects.filter(is_active=True).update(is_active=False)


class CourseRepository:
    def get_all(self) -> QuerySet[Course]:
        return Course.objects.select_related('study_program__faculty').all()

    def get_active(self) -> QuerySet[Course]:
        return Course.objects.filter(is_active=True)

    def get_by_id(self, course_id: int) -> Course | None:
        return Course.objects.filter(id=course_id).first()

    def get_by_study_program(self, sp_id: int) -> QuerySet[Course]:
        return Course.objects.filter(study_program_id=sp_id)

    def get_by_code(self, code: str) -> Course | None:
        return Course.objects.filter(code=code).first()

    def search(self, query: str) -> QuerySet[Course]:
        return Course.objects.filter(
            Q(code__icontains=query) | Q(name__icontains=query) | Q(description__icontains=query)
        )

    def create(self, **kwargs) -> Course:
        return Course.objects.create(**kwargs)

    def update(self, course_id: int, **kwargs) -> Course | None:
        updated = Course.objects.filter(id=course_id).update(**kwargs)
        if updated:
            return self.get_by_id(course_id)
        return None

    def delete(self, course_id: int) -> bool:
        return Course.objects.filter(id=course_id).delete()[0] > 0


class ClassRepository:
    def get_all(self) -> QuerySet[Class]:
        return Class.objects.select_related('course', 'semester__academic_year', 'lecturer').all()

    def get_active(self) -> QuerySet[Class]:
        return Class.objects.filter(is_active=True)

    def get_by_id(self, class_id: int) -> Class | None:
        return Class.objects.filter(id=class_id).first()

    def get_by_course(self, course_id: int) -> QuerySet[Class]:
        return Class.objects.filter(course_id=course_id)

    def get_by_semester(self, semester_id: int) -> QuerySet[Class]:
        return Class.objects.filter(semester_id=semester_id)

    def get_by_lecturer(self, lecturer_id: int) -> QuerySet[Class]:
        return Class.objects.filter(lecturer_id=lecturer_id)

    def search(self, query: str) -> QuerySet[Class]:
        return Class.objects.filter(
            Q(code__icontains=query) | Q(name__icontains=query) |
            Q(course__name__icontains=query) | Q(course__code__icontains=query) |
            Q(room__icontains=query)
        )

    def create(self, **kwargs) -> Class:
        return Class.objects.create(**kwargs)

    def update(self, class_id: int, **kwargs) -> Class | None:
        updated = Class.objects.filter(id=class_id).update(**kwargs)
        if updated:
            return self.get_by_id(class_id)
        return None

    def delete(self, class_id: int) -> bool:
        return Class.objects.filter(id=class_id).delete()[0] > 0


class EnrollmentRepository:
    def get_all(self) -> QuerySet[Enrollment]:
        return Enrollment.objects.select_related('student', 'class_enrolled__course', 'class_enrolled__semester').all()

    def get_by_id(self, enrollment_id: int) -> Enrollment | None:
        return Enrollment.objects.filter(id=enrollment_id).first()

    def get_by_student(self, student_id: int) -> QuerySet[Enrollment]:
        return Enrollment.objects.filter(student_id=student_id)

    def get_by_class(self, class_id: int) -> QuerySet[Enrollment]:
        return Enrollment.objects.filter(class_enrolled_id=class_id)

    def get_active_by_student(self, student_id: int) -> QuerySet[Enrollment]:
        return Enrollment.objects.filter(student_id=student_id, status='active')

    def get_enrollment(self, student_id: int, class_id: int) -> Enrollment | None:
        return Enrollment.objects.filter(student_id=student_id, class_enrolled_id=class_id).first()

    def create(self, **kwargs) -> Enrollment:
        return Enrollment.objects.create(**kwargs)

    def update(self, enrollment_id: int, **kwargs) -> Enrollment | None:
        updated = Enrollment.objects.filter(id=enrollment_id).update(**kwargs)
        if updated:
            return self.get_by_id(enrollment_id)
        return None

    def delete(self, enrollment_id: int) -> bool:
        return Enrollment.objects.filter(id=enrollment_id).delete()[0] > 0

    def count_enrolled(self, class_id: int) -> int:
        return Enrollment.objects.filter(class_enrolled_id=class_id, status='active').count()
