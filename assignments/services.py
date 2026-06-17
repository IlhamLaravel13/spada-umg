from django.db import transaction
from django.utils import timezone
from .repositories import AssignmentRepository, AssignmentSubmissionRepository


class AssignmentService:
    def __init__(self):
        self.repo = AssignmentRepository()

    def get_all(self):
        return self.repo.get_all()

    def get_by_id(self, assignment_id: int):
        return self.repo.get_by_id(assignment_id)

    def get_by_class(self, class_id: int):
        return self.repo.get_by_class(class_id)

    def create(self, **kwargs) -> dict:
        try:
            assignment = self.repo.create(**kwargs)
            return {'success': True, 'data': assignment}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def update(self, assignment_id: int, **kwargs) -> dict:
        try:
            assignment = self.repo.update(assignment_id, **kwargs)
            if assignment:
                return {'success': True, 'data': assignment}
            return {'success': False, 'error': 'Assignment not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def delete(self, assignment_id: int) -> dict:
        try:
            if self.repo.delete(assignment_id):
                return {'success': True, 'message': 'Assignment deleted successfully'}
            return {'success': False, 'error': 'Assignment not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def toggle_publish(self, assignment_id: int) -> dict:
        assignment = self.repo.get_by_id(assignment_id)
        if not assignment:
            return {'success': False, 'error': 'Assignment not found'}
        return self.update(assignment_id, is_published=not assignment.is_published)


class AssignmentSubmissionService:
    def __init__(self):
        self.submission_repo = AssignmentSubmissionRepository()
        self.assignment_repo = AssignmentRepository()

    def get_all(self):
        return self.submission_repo.get_all()

    def get_by_id(self, submission_id: int):
        return self.submission_repo.get_by_id(submission_id)

    def get_by_assignment(self, assignment_id: int):
        return self.submission_repo.get_by_assignment(assignment_id)

    def get_by_student(self, student_id: int):
        return self.submission_repo.get_by_student(student_id)

    def submit(self, student_id: int, assignment_id: int, **kwargs) -> dict:
        try:
            with transaction.atomic():
                assignment = self.assignment_repo.get_by_id(assignment_id)
                if not assignment:
                    return {'success': False, 'error': 'Assignment not found'}
                if not assignment.is_published:
                    return {'success': False, 'error': 'Assignment is not open for submissions'}
                if not assignment.allow_late_submission and assignment.is_past_due():
                    return {'success': False, 'error': 'Due date has passed'}
                latest = self.submission_repo.get_latest_by_student(student_id, assignment_id)
                attempt_number = (latest.attempt_number + 1) if latest else 1
                if attempt_number > assignment.max_attempts:
                    return {'success': False, 'error': 'Maximum attempts reached'}
                status = 'late' if assignment.is_past_due() else 'submitted'
                submission = self.submission_repo.create(
                    student_id=student_id,
                    assignment_id=assignment_id,
                    status=status,
                    attempt_number=attempt_number,
                    **{k: v for k, v in kwargs.items() if k in ['file', 'notes']},
                )
                return {'success': True, 'data': submission}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def grade(self, submission_id: int, score: float, feedback: str = '', graded_by_id: int = None) -> dict:
        try:
            submission = self.submission_repo.get_by_id(submission_id)
            if not submission:
                return {'success': False, 'error': 'Submission not found'}
            assignment = submission.assignment
            max_score = float(assignment.max_score) if assignment.max_score else 100
            if score > max_score:
                return {'success': False, 'error': f'Score cannot exceed {max_score}'}
            kwargs = {
                'score': score,
                'feedback': feedback,
                'status': 'graded',
                'graded_at': timezone.now(),
            }
            if graded_by_id:
                kwargs['graded_by_id'] = graded_by_id
            updated = self.submission_repo.update(submission_id, **kwargs)
            if updated:
                return {'success': True, 'data': updated}
            return {'success': False, 'error': 'Failed to grade submission'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_ungraded_by_assignment(self, assignment_id: int):
        return self.submission_repo.get_by_assignment(assignment_id).filter(score__isnull=True)
