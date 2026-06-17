from django.db import transaction
from django.utils import timezone
from .repositories import (
    FacultyRepository, StudyProgramRepository, AcademicYearRepository,
    SemesterRepository, CourseRepository, ClassRepository, EnrollmentRepository,
)


class FacultyService:
    def __init__(self):
        self.repo = FacultyRepository()

    def get_all(self):
        return self.repo.get_all()

    def get_active(self):
        return self.repo.get_active()

    def get_by_id(self, faculty_id: int):
        return self.repo.get_by_id(faculty_id)

    def get_by_slug(self, slug: str):
        return self.repo.get_by_slug(slug)

    def create(self, **kwargs) -> dict:
        try:
            faculty = self.repo.create(**kwargs)
            return {'success': True, 'data': faculty}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def update(self, faculty_id: int, **kwargs) -> dict:
        try:
            faculty = self.repo.update(faculty_id, **kwargs)
            if faculty:
                return {'success': True, 'data': faculty}
            return {'success': False, 'error': 'Faculty not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def delete(self, faculty_id: int) -> dict:
        try:
            if self.repo.delete(faculty_id):
                return {'success': True, 'message': 'Faculty deleted successfully'}
            return {'success': False, 'error': 'Faculty not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def toggle_active(self, faculty_id: int) -> dict:
        faculty = self.repo.get_by_id(faculty_id)
        if not faculty:
            return {'success': False, 'error': 'Faculty not found'}
        new_status = not faculty.is_active
        return self.update(faculty_id, is_active=new_status)


class StudyProgramService:
    def __init__(self):
        self.repo = StudyProgramRepository()

    def get_all(self):
        return self.repo.get_all()

    def get_active(self):
        return self.repo.get_active()

    def get_by_id(self, sp_id: int):
        return self.repo.get_by_id(sp_id)

    def get_by_faculty(self, faculty_id: int):
        return self.repo.get_by_faculty(faculty_id)

    def create(self, **kwargs) -> dict:
        try:
            sp = self.repo.create(**kwargs)
            return {'success': True, 'data': sp}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def update(self, sp_id: int, **kwargs) -> dict:
        try:
            sp = self.repo.update(sp_id, **kwargs)
            if sp:
                return {'success': True, 'data': sp}
            return {'success': False, 'error': 'Study Program not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def delete(self, sp_id: int) -> dict:
        try:
            if self.repo.delete(sp_id):
                return {'success': True, 'message': 'Study Program deleted successfully'}
            return {'success': False, 'error': 'Study Program not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}


class CourseService:
    def __init__(self):
        self.repo = CourseRepository()

    def get_all(self):
        return self.repo.get_all()

    def get_active(self):
        return self.repo.get_active()

    def get_by_id(self, course_id: int):
        return self.repo.get_by_id(course_id)

    def get_by_study_program(self, sp_id: int):
        return self.repo.get_by_study_program(sp_id)

    def create(self, **kwargs) -> dict:
        try:
            course = self.repo.create(**kwargs)
            return {'success': True, 'data': course}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def update(self, course_id: int, **kwargs) -> dict:
        try:
            course = self.repo.update(course_id, **kwargs)
            if course:
                return {'success': True, 'data': course}
            return {'success': False, 'error': 'Course not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def delete(self, course_id: int) -> dict:
        try:
            if self.repo.delete(course_id):
                return {'success': True, 'message': 'Course deleted successfully'}
            return {'success': False, 'error': 'Course not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}


class ClassService:
    def __init__(self):
        self.repo = ClassRepository()

    def get_all(self):
        return self.repo.get_all()

    def get_active(self):
        return self.repo.get_active()

    def get_by_id(self, class_id: int):
        return self.repo.get_by_id(class_id)

    def get_by_course(self, course_id: int):
        return self.repo.get_by_course(course_id)

    def get_by_semester(self, semester_id: int):
        return self.repo.get_by_semester(semester_id)

    def get_by_lecturer(self, lecturer_id: int):
        return self.repo.get_by_lecturer(lecturer_id)

    def create(self, **kwargs) -> dict:
        try:
            class_obj = self.repo.create(**kwargs)
            return {'success': True, 'data': class_obj}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def update(self, class_id: int, **kwargs) -> dict:
        try:
            class_obj = self.repo.update(class_id, **kwargs)
            if class_obj:
                return {'success': True, 'data': class_obj}
            return {'success': False, 'error': 'Class not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def delete(self, class_id: int) -> dict:
        try:
            if self.repo.delete(class_id):
                return {'success': True, 'message': 'Class deleted successfully'}
            return {'success': False, 'error': 'Class not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}


class EnrollmentService:
    def __init__(self):
        self.enrollment_repo = EnrollmentRepository()
        self.class_repo = ClassRepository()

    def get_all(self):
        return self.enrollment_repo.get_all()

    def get_by_id(self, enrollment_id: int):
        return self.enrollment_repo.get_by_id(enrollment_id)

    def get_by_student(self, student_id: int):
        return self.enrollment_repo.get_by_student(student_id)

    def get_by_class(self, class_id: int):
        return self.enrollment_repo.get_by_class(class_id)

    def enroll_student(self, student_id: int, class_id: int) -> dict:
        try:
            with transaction.atomic():
                class_obj = self.class_repo.get_by_id(class_id)
                if not class_obj:
                    return {'success': False, 'error': 'Class not found'}
                if not class_obj.is_active:
                    return {'success': False, 'error': 'Class is not active'}
                existing = self.enrollment_repo.get_enrollment(student_id, class_id)
                if existing:
                    return {'success': False, 'error': 'Student is already enrolled in this class'}
                enrolled_count = self.enrollment_repo.count_enrolled(class_id)
                if enrolled_count >= class_obj.max_students:
                    return {'success': False, 'error': 'Class is full'}
                enrollment = self.enrollment_repo.create(
                    student_id=student_id,
                    class_enrolled_id=class_id,
                    status='active',
                )
                return {'success': True, 'data': enrollment}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def withdraw_student(self, enrollment_id: int) -> dict:
        try:
            enrollment = self.enrollment_repo.get_by_id(enrollment_id)
            if not enrollment:
                return {'success': False, 'error': 'Enrollment not found'}
            result = self.enrollment_repo.update(enrollment_id, status='dropped')
            if result:
                return {'success': True, 'message': 'Student withdrawn successfully'}
            return {'success': False, 'error': 'Failed to withdraw student'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def update_grade(self, enrollment_id: int, grade_final: float = None, grade_letter: str = '') -> dict:
        try:
            kwargs = {}
            if grade_final is not None:
                kwargs['grade_final'] = grade_final
            if grade_letter:
                kwargs['grade_letter'] = grade_letter
            if not kwargs:
                return {'success': False, 'error': 'No grade data provided'}
            enrollment = self.enrollment_repo.update(enrollment_id, **kwargs)
            if enrollment:
                return {'success': True, 'data': enrollment}
            return {'success': False, 'error': 'Enrollment not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def bulk_enroll(self, student_ids: list, class_id: int) -> dict:
        results = {'success': [], 'failed': []}
        for student_id in student_ids:
            result = self.enroll_student(student_id, class_id)
            if result['success']:
                results['success'].append(student_id)
            else:
                results['failed'].append({'student_id': student_id, 'error': result['error']})
        return results


class SemesterService:
    def __init__(self):
        self.semester_repo = SemesterRepository()
        self.academic_year_repo = AcademicYearRepository()

    def get_all(self):
        return self.semester_repo.get_all()

    def get_active(self):
        return self.semester_repo.get_active()

    def get_by_id(self, semester_id: int):
        return self.semester_repo.get_by_id(semester_id)

    def create(self, **kwargs) -> dict:
        try:
            semester = self.semester_repo.create(**kwargs)
            return {'success': True, 'data': semester}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def update(self, semester_id: int, **kwargs) -> dict:
        try:
            semester = self.semester_repo.update(semester_id, **kwargs)
            if semester:
                return {'success': True, 'data': semester}
            return {'success': False, 'error': 'Semester not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def delete(self, semester_id: int) -> dict:
        try:
            if self.semester_repo.delete(semester_id):
                return {'success': True, 'message': 'Semester deleted successfully'}
            return {'success': False, 'error': 'Semester not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def activate(self, semester_id: int) -> dict:
        try:
            with transaction.atomic():
                self.semester_repo.deactivate_all()
                self.academic_year_repo.deactivate_all()
                semester = self.semester_repo.update(semester_id, is_active=True)
                if not semester:
                    return {'success': False, 'error': 'Semester not found'}
                if semester.academic_year:
                    self.academic_year_repo.update(semester.academic_year.id, is_active=True)
                return {'success': True, 'data': semester, 'message': 'Semester activated successfully'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def deactivate(self, semester_id: int) -> dict:
        try:
            semester = self.semester_repo.update(semester_id, is_active=False)
            if semester:
                return {'success': True, 'message': 'Semester deactivated successfully'}
            return {'success': False, 'error': 'Semester not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_by_academic_year(self, academic_year_id: int):
        return self.semester_repo.get_by_academic_year(academic_year_id)


class AcademicYearService:
    def __init__(self):
        self.repo = AcademicYearRepository()

    def get_all(self):
        return self.repo.get_all()

    def get_active(self):
        return self.repo.get_active()

    def get_by_id(self, ay_id: int):
        return self.repo.get_by_id(ay_id)

    def create(self, **kwargs) -> dict:
        try:
            ay = self.repo.create(**kwargs)
            return {'success': True, 'data': ay}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def update(self, ay_id: int, **kwargs) -> dict:
        try:
            ay = self.repo.update(ay_id, **kwargs)
            if ay:
                return {'success': True, 'data': ay}
            return {'success': False, 'error': 'Academic Year not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def delete(self, ay_id: int) -> dict:
        try:
            if self.repo.delete(ay_id):
                return {'success': True, 'message': 'Academic Year deleted successfully'}
            return {'success': False, 'error': 'Academic Year not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
