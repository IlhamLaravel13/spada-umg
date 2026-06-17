from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from .repositories import (
    QuizRepository, QuizQuestionRepository, QuizAnswerRepository,
    QuizAttemptRepository, QuizResponseRepository,
)


class QuizService:
    def __init__(self):
        self.repo = QuizRepository()

    def get_all(self):
        return self.repo.get_all()

    def get_by_id(self, quiz_id: int):
        return self.repo.get_by_id(quiz_id)

    def get_by_class(self, class_id: int):
        return self.repo.get_by_class(class_id)

    def create(self, **kwargs) -> dict:
        try:
            quiz = self.repo.create(**kwargs)
            return {'success': True, 'data': quiz}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def update(self, quiz_id: int, **kwargs) -> dict:
        try:
            quiz = self.repo.update(quiz_id, **kwargs)
            if quiz:
                return {'success': True, 'data': quiz}
            return {'success': False, 'error': 'Quiz not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def delete(self, quiz_id: int) -> dict:
        try:
            if self.repo.delete(quiz_id):
                return {'success': True, 'message': 'Quiz deleted successfully'}
            return {'success': False, 'error': 'Quiz not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def toggle_publish(self, quiz_id: int) -> dict:
        quiz = self.repo.get_by_id(quiz_id)
        if not quiz:
            return {'success': False, 'error': 'Quiz not found'}
        return self.update(quiz_id, is_published=not quiz.is_published)

    def duplicate(self, quiz_id: int) -> dict:
        try:
            with transaction.atomic():
                original = self.repo.get_by_id(quiz_id)
                if not original:
                    return {'success': False, 'error': 'Quiz not found'}
                new_quiz = self.repo.create(
                    class_meta=original.class_meta,
                    title=f"{original.title} (Copy)",
                    description=original.description,
                    time_limit_minutes=original.time_limit_minutes,
                    max_attempts=original.max_attempts,
                    passing_score=original.passing_score,
                    shuffle_questions=original.shuffle_questions,
                    show_result_immediately=original.show_result_immediately,
                    is_published=False,
                    due_date=original.due_date,
                    created_by=original.created_by,
                )
                for question in original.questions.all():
                    new_q = QuizQuestion.objects.create(
                        quiz=new_quiz,
                        question_text=question.question_text,
                        question_type=question.question_type,
                        points=question.points,
                        order=question.order,
                    )
                    for answer in question.answers.all():
                        QuizAnswer.objects.create(
                            question=new_q,
                            answer_text=answer.answer_text,
                            is_correct=answer.is_correct,
                        )
                return {'success': True, 'data': new_quiz}
        except Exception as e:
            return {'success': False, 'error': str(e)}


class QuizAttemptService:
    def __init__(self):
        self.attempt_repo = QuizAttemptRepository()
        self.response_repo = QuizResponseRepository()
        self.quiz_repo = QuizRepository()
        self.question_repo = QuizQuestionRepository()

    def start_attempt(self, student_id: int, quiz_id: int) -> dict:
        try:
            with transaction.atomic():
                quiz = self.quiz_repo.get_by_id(quiz_id)
                if not quiz:
                    return {'success': False, 'error': 'Quiz not found'}
                if not quiz.is_published:
                    return {'success': False, 'error': 'Quiz is not available'}
                if quiz.is_past_due():
                    return {'success': False, 'error': 'Quiz due date has passed'}
                attempt_count = self.attempt_repo.count_attempts(student_id, quiz_id)
                if attempt_count >= quiz.max_attempts:
                    return {'success': False, 'error': 'Maximum attempts reached'}
                attempt = self.attempt_repo.create(
                    student_id=student_id,
                    quiz_id=quiz_id,
                )
                return {'success': True, 'data': attempt}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def submit_answer(self, attempt_id: int, question_id: int, selected_answer_id: int = None, essay_answer: str = '') -> dict:
        try:
            attempt = self.attempt_repo.get_by_id(attempt_id)
            if not attempt or attempt.is_completed():
                return {'success': False, 'error': 'Attempt not found or already completed'}
            question = self.question_repo.get_by_id(question_id)
            if not question or question.quiz_id != attempt.quiz_id:
                return {'success': False, 'error': 'Invalid question'}

            is_correct = False
            points_earned = Decimal('0')

            if question.question_type == 'essay':
                points_earned = Decimal('0')
            elif selected_answer_id:
                answer = QuizAnswer.objects.filter(id=selected_answer_id, question_id=question_id).first()
                if answer:
                    is_correct = answer.is_correct
                    points_earned = Decimal(question.points) if is_correct else Decimal('0')

            response, created = QuizResponse.objects.get_or_create(
                attempt_id=attempt_id,
                question_id=question_id,
                defaults={
                    'selected_answer_id': selected_answer_id,
                    'essay_answer': essay_answer,
                    'is_correct': is_correct,
                    'points_earned': points_earned,
                },
            )
            if not created:
                self.response_repo.update(
                    response.id,
                    selected_answer_id=selected_answer_id,
                    essay_answer=essay_answer,
                    is_correct=is_correct,
                    points_earned=points_earned,
                )

            return {'success': True, 'data': response}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def complete_attempt(self, attempt_id: int, manual_grades: dict = None) -> dict:
        try:
            with transaction.atomic():
                attempt = self.attempt_repo.get_by_id(attempt_id)
                if not attempt:
                    return {'success': False, 'error': 'Attempt not found'}
                if attempt.is_completed():
                    return {'success': False, 'error': 'Attempt already completed'}

                responses = self.response_repo.get_by_attempt(attempt_id)
                total_points = Decimal('0')
                all_graded = True

                for response in responses:
                    if manual_grades and str(response.question_id) in manual_grades:
                        grade = Decimal(str(manual_grades[str(response.question_id)]))
                        self.response_repo.update(
                            response.id,
                            points_earned=grade,
                            is_correct=grade > 0,
                        )
                        total_points += grade
                    elif response.question.question_type == 'essay':
                        all_graded = False
                    else:
                        total_points += response.points_earned

                if not all_graded:
                    return {'success': False, 'error': 'Essay questions need manual grading', 'data': attempt}

                quiz_total = attempt.quiz.total_points()
                score = (total_points / quiz_total * 100) if quiz_total > 0 else Decimal('0')
                is_passed = score >= Decimal(str(attempt.quiz.passing_score))

                self.attempt_repo.update(
                    attempt_id,
                    score=score,
                    completed_at=timezone.now(),
                    is_passed=is_passed,
                )

                attempt.refresh_from_db()
                return {'success': True, 'data': attempt}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def grade_essay(self, attempt_id: int, question_id: int, points: float) -> dict:
        try:
            response = QuizResponse.objects.filter(
                attempt_id=attempt_id, question_id=question_id
            ).first()
            if not response:
                return {'success': False, 'error': 'Response not found'}
            response = self.response_repo.update(
                response.id,
                points_earned=Decimal(str(points)),
                is_correct=points > 0,
            )
            if response:
                return {'success': True, 'data': response}
            return {'success': False, 'error': 'Failed to grade essay'}
        except Exception as e:
            return {'success': False, 'error': str(e)}


class QuizQuestionService:
    def __init__(self):
        self.repo = QuizQuestionRepository()
        self.answer_repo = QuizAnswerRepository()

    def create_with_answers(self, quiz_id: int, question_text: str, question_type: str,
                            points: int = 10, order: int = 0, answers: list = None) -> dict:
        try:
            with transaction.atomic():
                question = self.repo.create(
                    quiz_id=quiz_id, question_text=question_text,
                    question_type=question_type, points=points, order=order,
                )
                if answers:
                    answer_objs = [
                        QuizAnswer(question=question, answer_text=a.get('text', ''),
                                    is_correct=a.get('is_correct', False))
                        for a in answers
                    ]
                    self.answer_repo.bulk_create(answer_objs)
                return {'success': True, 'data': question}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def update_with_answers(self, question_id: int, **kwargs) -> dict:
        try:
            with transaction.atomic():
                answers_data = kwargs.pop('answers', None)
                question = self.repo.update(question_id, **kwargs)
                if not question:
                    return {'success': False, 'error': 'Question not found'}
                if answers_data is not None:
                    self.answer_repo.get_by_question(question_id).delete()
                    answer_objs = [
                        QuizAnswer(question=question, answer_text=a.get('text', ''),
                                    is_correct=a.get('is_correct', False))
                        for a in answers_data
                    ]
                    self.answer_repo.bulk_create(answer_objs)
                return {'success': True, 'data': question}
        except Exception as e:
            return {'success': False, 'error': str(e)}
