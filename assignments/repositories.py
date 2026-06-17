from django.db.models import QuerySet, Q
from django.utils import timezone
from .models import Assignment, AssignmentSubmission, AssignmentSubmissionAttachment


class AssignmentRepository:
    def get_all(self) -> QuerySet[Assignment]:
        return Assignment.objects.select_related('class_meta__course', 'created_by').all()

    def get_by_id(self, assignment_id: int) -> Assignment | None:
        return Assignment.objects.filter(id=assignment_id).first()

    def get_by_class(self, class_id: int) -> QuerySet[Assignment]:
        return Assignment.objects.filter(class_meta_id=class_id)

    def get_published(self) -> QuerySet[Assignment]:
        return Assignment.objects.filter(is_published=True)

    def get_past_due(self) -> QuerySet[Assignment]:
        return Assignment.objects.filter(due_date__lt=timezone.now())

    def search(self, query: str) -> QuerySet[Assignment]:
        return Assignment.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    def create(self, **kwargs) -> Assignment:
        return Assignment.objects.create(**kwargs)

    def update(self, assignment_id: int, **kwargs) -> Assignment | None:
        updated = Assignment.objects.filter(id=assignment_id).update(**kwargs)
        if updated:
            return self.get_by_id(assignment_id)
        return None

    def delete(self, assignment_id: int) -> bool:
        return Assignment.objects.filter(id=assignment_id).delete()[0] > 0

    def count_by_class(self, class_id: int) -> int:
        return Assignment.objects.filter(class_meta_id=class_id).count()


class AssignmentSubmissionRepository:
    def get_all(self) -> QuerySet[AssignmentSubmission]:
        return AssignmentSubmission.objects.select_related('assignment', 'student', 'graded_by').all()

    def get_by_id(self, submission_id: int) -> AssignmentSubmission | None:
        return AssignmentSubmission.objects.filter(id=submission_id).first()

    def get_by_assignment(self, assignment_id: int) -> QuerySet[AssignmentSubmission]:
        return AssignmentSubmission.objects.filter(assignment_id=assignment_id)

    def get_by_student(self, student_id: int) -> QuerySet[AssignmentSubmission]:
        return AssignmentSubmission.objects.filter(student_id=student_id)

    def get_by_student_and_assignment(self, student_id: int, assignment_id: int) -> QuerySet[AssignmentSubmission]:
        return AssignmentSubmission.objects.filter(student_id=student_id, assignment_id=assignment_id)

    def get_graded(self) -> QuerySet[AssignmentSubmission]:
        return AssignmentSubmission.objects.filter(status='graded')

    def get_ungraded(self) -> QuerySet[AssignmentSubmission]:
        return AssignmentSubmission.objects.filter(score__isnull=True).exclude(status='graded')

    def get_latest_by_student(self, student_id: int, assignment_id: int) -> AssignmentSubmission | None:
        return AssignmentSubmission.objects.filter(
            student_id=student_id, assignment_id=assignment_id
        ).order_by('-attempt_number').first()

    def create(self, **kwargs) -> AssignmentSubmission:
        return AssignmentSubmission.objects.create(**kwargs)

    def update(self, submission_id: int, **kwargs) -> AssignmentSubmission | None:
        updated = AssignmentSubmission.objects.filter(id=submission_id).update(**kwargs)
        if updated:
            return self.get_by_id(submission_id)
        return None

    def delete(self, submission_id: int) -> bool:
        return AssignmentSubmission.objects.filter(id=submission_id).delete()[0] > 0

    def count_by_assignment(self, assignment_id: int) -> int:
        return AssignmentSubmission.objects.filter(assignment_id=assignment_id).count()

    def count_ungraded_by_assignment(self, assignment_id: int) -> int:
        return AssignmentSubmission.objects.filter(assignment_id=assignment_id, score__isnull=True).count()
