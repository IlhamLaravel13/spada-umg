from django.db.models import QuerySet, Q, Prefetch
from django.utils import timezone
from .models import Quiz, QuizQuestion, QuizAnswer, QuizAttempt, QuizResponse


class QuizRepository:
    def get_all(self) -> QuerySet[Quiz]:
        return Quiz.objects.select_related('class_meta__course', 'created_by').all()

    def get_by_id(self, quiz_id: int) -> Quiz | None:
        return Quiz.objects.filter(id=quiz_id).first()

    def get_by_class(self, class_id: int) -> QuerySet[Quiz]:
        return Quiz.objects.filter(class_meta_id=class_id)

    def get_published(self) -> QuerySet[Quiz]:
        return Quiz.objects.filter(is_published=True)

    def search(self, query: str) -> QuerySet[Quiz]:
        return Quiz.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    def create(self, **kwargs) -> Quiz:
        return Quiz.objects.create(**kwargs)

    def update(self, quiz_id: int, **kwargs) -> Quiz | None:
        updated = Quiz.objects.filter(id=quiz_id).update(**kwargs)
        if updated:
            return self.get_by_id(quiz_id)
        return None

    def delete(self, quiz_id: int) -> bool:
        return Quiz.objects.filter(id=quiz_id).delete()[0] > 0


class QuizQuestionRepository:
    def get_by_quiz(self, quiz_id: int) -> QuerySet[QuizQuestion]:
        return QuizQuestion.objects.filter(quiz_id=quiz_id).order_by('order', 'id')

    def get_by_id(self, question_id: int) -> QuizQuestion | None:
        return QuizQuestion.objects.filter(id=question_id).first()

    def get_with_answers(self, quiz_id: int) -> QuerySet[QuizQuestion]:
        return QuizQuestion.objects.filter(quiz_id=quiz_id).prefetch_related('answers')

    def create(self, **kwargs) -> QuizQuestion:
        return QuizQuestion.objects.create(**kwargs)

    def update(self, question_id: int, **kwargs) -> QuizQuestion | None:
        updated = QuizQuestion.objects.filter(id=question_id).update(**kwargs)
        if updated:
            return self.get_by_id(question_id)
        return None

    def delete(self, question_id: int) -> bool:
        return QuizQuestion.objects.filter(id=question_id).delete()[0] > 0

    def reorder(self, quiz_id: int, question_ids: list) -> None:
        for idx, qid in enumerate(question_ids):
            QuizQuestion.objects.filter(id=qid, quiz_id=quiz_id).update(order=idx)


class QuizAnswerRepository:
    def get_by_question(self, question_id: int) -> QuerySet[QuizAnswer]:
        return QuizAnswer.objects.filter(question_id=question_id)

    def get_by_id(self, answer_id: int) -> QuizAnswer | None:
        return QuizAnswer.objects.filter(id=answer_id).first()

    def get_correct_answers(self, question_id: int) -> QuerySet[QuizAnswer]:
        return QuizAnswer.objects.filter(question_id=question_id, is_correct=True)

    def create(self, **kwargs) -> QuizAnswer:
        return QuizAnswer.objects.create(**kwargs)

    def update(self, answer_id: int, **kwargs) -> QuizAnswer | None:
        updated = QuizAnswer.objects.filter(id=answer_id).update(**kwargs)
        if updated:
            return self.get_by_id(answer_id)
        return None

    def delete(self, answer_id: int) -> bool:
        return QuizAnswer.objects.filter(id=answer_id).delete()[0] > 0

    def bulk_create(self, answers: list) -> list:
        return QuizAnswer.objects.bulk_create(answers)


class QuizAttemptRepository:
    def get_all(self) -> QuerySet[QuizAttempt]:
        return QuizAttempt.objects.select_related('quiz', 'student').all()

    def get_by_id(self, attempt_id: int) -> QuizAttempt | None:
        return QuizAttempt.objects.filter(id=attempt_id).first()

    def get_by_quiz(self, quiz_id: int) -> QuerySet[QuizAttempt]:
        return QuizAttempt.objects.filter(quiz_id=quiz_id)

    def get_by_student(self, student_id: int) -> QuerySet[QuizAttempt]:
        return QuizAttempt.objects.filter(student_id=student_id)

    def get_by_student_and_quiz(self, student_id: int, quiz_id: int) -> QuerySet[QuizAttempt]:
        return QuizAttempt.objects.filter(student_id=student_id, quiz_id=quiz_id)

    def count_attempts(self, student_id: int, quiz_id: int) -> int:
        return QuizAttempt.objects.filter(student_id=student_id, quiz_id=quiz_id).count()

    def create(self, **kwargs) -> QuizAttempt:
        return QuizAttempt.objects.create(**kwargs)

    def update(self, attempt_id: int, **kwargs) -> QuizAttempt | None:
        updated = QuizAttempt.objects.filter(id=attempt_id).update(**kwargs)
        if updated:
            return self.get_by_id(attempt_id)
        return None


class QuizResponseRepository:
    def get_by_attempt(self, attempt_id: int) -> QuerySet[QuizResponse]:
        return QuizResponse.objects.filter(attempt_id=attempt_id).select_related('question', 'selected_answer')

    def get_by_id(self, response_id: int) -> QuizResponse | None:
        return QuizResponse.objects.filter(id=response_id).first()

    def create(self, **kwargs) -> QuizResponse:
        return QuizResponse.objects.create(**kwargs)

    def bulk_create(self, responses: list) -> list:
        return QuizResponse.objects.bulk_create(responses)
