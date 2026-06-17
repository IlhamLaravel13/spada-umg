import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, View
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.db.models import Q
from django.utils import timezone

from .models import Quiz, QuizQuestion, QuizAnswer, QuizAttempt, QuizResponse
from .services import QuizService, QuizAttemptService, QuizQuestionService
from .repositories import QuizRepository, QuizQuestionRepository, QuizAnswerRepository


def is_admin_or_dosen(user):
    return user.is_authenticated and (user.is_admin() or user.is_dosen())


def is_mahasiswa(user):
    return user.is_authenticated and user.is_mahasiswa()


class HTMXMixin:
    def htmx_render(self, template, context):
        if self.request.headers.get('HX-Request'):
            return render(self.request, template, context)
        return render(self.request, template, context)


class QuizListView(HTMXMixin, ListView):
    model = Quiz
    template_name = 'quizzes/quiz_list.html'
    context_object_name = 'quizzes'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        class_id = self.request.GET.get('class_id')
        status = self.request.GET.get('status')

        if user.is_authenticated and user.is_dosen():
            qs = Quiz.objects.filter(class_meta__lecturer=user)
        elif user.is_authenticated and user.is_mahasiswa():
            enrolled_classes = user.enrollments.filter(status='active').values_list('class_enrolled_id', flat=True)
            qs = Quiz.objects.filter(class_meta_id__in=enrolled_classes, is_published=True)
        else:
            qs = Quiz.objects.all()

        if class_id:
            qs = qs.filter(class_meta_id=class_id)
        if status == 'past_due':
            qs = qs.filter(due_date__lt=timezone.now())
        elif status == 'open':
            qs = qs.filter(due_date__gte=timezone.now(), is_published=True)

        query = self.request.GET.get('q')
        if query:
            qs = qs.filter(Q(title__icontains=query) | Q(description__icontains=query))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['class_id'] = self.request.GET.get('class_id')
        return context


class QuizDetailView(DetailView):
    model = Quiz
    template_name = 'quizzes/quiz_detail.html'
    context_object_name = 'quiz'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        quiz = self.object

        if user.is_authenticated:
            context['user_attempts'] = QuizAttempt.objects.filter(
                student=user, quiz=quiz
            ).order_by('-started_at')

            remaining = quiz.max_attempts - context['user_attempts'].count()
            context['remaining_attempts'] = max(0, remaining)
            context['can_take'] = (
                user.is_mahasiswa() and
                quiz.is_published and
                not quiz.is_past_due() and
                remaining > 0
            )

        context['question_count'] = quiz.questions.count()
        context['total_points'] = quiz.total_points()
        return context


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class QuizCreateView(CreateView):
    model = Quiz
    template_name = 'quizzes/quiz_form.html'
    fields = [
        'class_meta', 'title', 'description', 'time_limit_minutes', 'max_attempts',
        'passing_score', 'shuffle_questions', 'show_result_immediately',
        'is_published', 'due_date',
    ]
    success_url = reverse_lazy('quizzes:quiz_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        result = QuizService().create(**form.cleaned_data, created_by=self.request.user)
        if result['success']:
            messages.success(self.request, 'Quiz created successfully.')
            if self.request.headers.get('HX-Request'):
                return HttpResponse(status=201, headers={'HX-Trigger': 'quizListChanged'})
            return redirect(self.success_url)
        messages.error(self.request, result['error'])
        return self.form_invalid(form)

    def form_invalid(self, form):
        if self.request.headers.get('HX-Request'):
            html = render_to_string(self.template_name, {'form': form}, request=self.request)
            return HttpResponse(html, status=422)
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['class_id'] = self.request.GET.get('class_id')
        return context


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class QuizUpdateView(UpdateView):
    model = Quiz
    template_name = 'quizzes/quiz_form.html'
    fields = [
        'class_meta', 'title', 'description', 'time_limit_minutes', 'max_attempts',
        'passing_score', 'shuffle_questions', 'show_result_immediately',
        'is_published', 'due_date',
    ]
    success_url = reverse_lazy('quizzes:quiz_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        return context

    def form_valid(self, form):
        result = QuizService().update(self.get_object().id, **form.cleaned_data)
        if result['success']:
            messages.success(self.request, 'Quiz updated successfully.')
            if self.request.headers.get('HX-Request'):
                return HttpResponse(status=200, headers={'HX-Trigger': 'quizListChanged'})
            return redirect(self.success_url)
        messages.error(self.request, result['error'])
        return self.form_invalid(form)

    def form_invalid(self, form):
        if self.request.headers.get('HX-Request'):
            html = render_to_string(self.template_name, {'form': form, 'object': self.get_object(), 'is_update': True}, request=self.request)
            return HttpResponse(html, status=422)
        return super().form_invalid(form)


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class QuizDeleteView(DeleteView):
    model = Quiz
    success_url = reverse_lazy('quizzes:quiz_list')

    def delete(self, request, *args, **kwargs):
        result = QuizService().delete(kwargs.get('pk'))
        if result['success']:
            messages.success(request, result['message'])
        else:
            messages.error(request, result['error'])
        if request.headers.get('HX-Request'):
            return HttpResponse(status=200, headers={'HX-Trigger': 'quizListChanged'})
        return redirect(self.success_url)


@method_decorator([login_required, user_passes_test(is_mahasiswa)], name='dispatch')
class QuizTakeView(DetailView):
    model = Quiz
    template_name = 'quizzes/quiz_take.html'
    context_object_name = 'quiz'

    def get(self, request, *args, **kwargs):
        quiz = self.get_object()
        if not quiz.is_published or quiz.is_past_due():
            messages.error(request, 'This quiz is not available.')
            return redirect('quizzes:quiz_detail', pk=quiz.pk)
        attempt_count = QuizAttempt.objects.filter(student=request.user, quiz=quiz).count()
        if attempt_count >= quiz.max_attempts:
            messages.error(request, 'Maximum attempts reached.')
            return redirect('quizzes:quiz_detail', pk=quiz.pk)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quiz = self.object

        attempt, created = QuizAttempt.objects.get_or_create(
            student=self.request.user, quiz=quiz, completed_at__isnull=True,
            defaults={'student': self.request.user, 'quiz': quiz},
        )
        context['attempt'] = attempt

        questions = quiz.questions.prefetch_related('answers').all()
        if quiz.shuffle_questions:
            questions = list(questions)
            import random
            random.shuffle(questions)
        context['questions'] = questions

        existing_responses = {
            r.question_id: r for r in QuizResponse.objects.filter(attempt=attempt)
        }
        context['existing_responses'] = existing_responses
        context['time_limit'] = quiz.time_limit_minutes * 60
        return context


@method_decorator([login_required, user_passes_test(is_mahasiswa)], name='dispatch')
class QuizSubmitView(View):
    def post(self, request, *args, **kwargs):
        quiz = get_object_or_404(Quiz, pk=kwargs.get('pk'))
        attempt = QuizAttempt.objects.filter(
            student=request.user, quiz=quiz, completed_at__isnull=True
        ).first()

        if not attempt:
            messages.error(request, 'No active attempt found.')
            return redirect('quizzes:quiz_detail', pk=quiz.pk)

        service = QuizAttemptService()
        for key, value in request.POST.items():
            if key.startswith('question_'):
                qid = int(key.replace('question_', ''))
                if value:
                    try:
                        aid = int(value)
                        service.submit_answer(attempt.id, qid, selected_answer_id=aid)
                    except ValueError:
                        service.submit_answer(attempt.id, qid, essay_answer=value)

        result = service.complete_attempt(attempt.id)
        if result['success']:
            messages.success(request, 'Quiz submitted successfully!')
            return redirect('quizzes:quiz_result', pk=quiz.pk, attempt_pk=attempt.id)

        messages.error(request, result.get('error', 'Failed to submit quiz. Please try again.'))
        return redirect('quizzes:quiz_take', pk=quiz.pk)


class QuizResultView(DetailView):
    model = QuizAttempt
    template_name = 'quizzes/quiz_result.html'
    context_object_name = 'attempt'
    pk_url_kwarg = 'attempt_pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attempt = self.object
        context['quiz'] = attempt.quiz
        context['responses'] = QuizResponse.objects.filter(attempt=attempt).select_related('question', 'selected_answer')
        correct = context['responses'].filter(is_correct=True).count()
        context['correct_count'] = correct
        context['total_questions'] = attempt.quiz.questions.count()
        return context


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class QuizGradeListView(ListView):
    model = QuizAttempt
    template_name = 'quizzes/quiz_grade.html'
    context_object_name = 'attempts'
    paginate_by = 20

    def get_queryset(self):
        qs = QuizAttempt.objects.select_related('student', 'quiz').all()
        quiz_id = self.request.GET.get('quiz_id')
        student_query = self.request.GET.get('q')

        if quiz_id:
            qs = qs.filter(quiz_id=quiz_id)
        if student_query:
            qs = qs.filter(
                Q(student__username__icontains=student_query) |
                Q(student__nim__icontains=student_query) |
                Q(student__first_name__icontains=student_query)
            )

        user = self.request.user
        if user.is_dosen():
            qs = qs.filter(quiz__class_meta__lecturer=user)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['quiz_id'] = self.request.GET.get('quiz_id')
        return context


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class QuizGradeEssayView(View):
    def post(self, request, *args, **kwargs):
        attempt_id = kwargs.get('attempt_pk')
        question_id = kwargs.get('question_pk')
        points = request.POST.get('points', 0)

        try:
            points = float(points)
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Invalid points value'})

        service = QuizAttemptService()
        result = service.grade_essay(attempt_id, question_id, points)
        if result['success']:
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'error': result.get('error', 'Failed to grade')})


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class QuestionCreateView(CreateView):
    model = QuizQuestion
    template_name = 'quizzes/question_form.html'
    fields = ['quiz', 'question_text', 'question_type', 'points', 'order']

    def get_initial(self):
        initial = super().get_initial()
        quiz_id = self.request.GET.get('quiz_id') or self.kwargs.get('quiz_pk')
        if quiz_id:
            initial['quiz'] = quiz_id
            quiz = get_object_or_404(Quiz, pk=quiz_id)
            initial['order'] = quiz.questions.count() + 1
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quiz_id = self.request.GET.get('quiz_id') or self.kwargs.get('quiz_pk')
        if quiz_id:
            context['quiz'] = get_object_or_404(Quiz, pk=quiz_id)
        context['is_update'] = False
        return context

    def form_valid(self, form):
        question = form.save()
        answers_data = self.request.POST.getlist('answer_text')
        correct_answers = self.request.POST.getlist('is_correct')

        for i, text in enumerate(answers_data):
            if text.strip():
                QuizAnswer.objects.create(
                    question=question,
                    answer_text=text,
                    is_correct=str(i) in correct_answers,
                )

        messages.success(self.request, 'Question added successfully.')
        return redirect('quizzes:quiz_detail', pk=question.quiz_id)


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class QuestionUpdateView(UpdateView):
    model = QuizQuestion
    template_name = 'quizzes/question_form.html'
    fields = ['question_text', 'question_type', 'points', 'order']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        context['quiz'] = self.get_object().quiz
        context['answers'] = self.get_object().answers.all()
        return context

    def form_valid(self, form):
        question = form.save()
        question.answers.all().delete()
        answers_data = self.request.POST.getlist('answer_text')
        correct_answers = self.request.POST.getlist('is_correct')
        for i, text in enumerate(answers_data):
            if text.strip():
                QuizAnswer.objects.create(
                    question=question,
                    answer_text=text,
                    is_correct=str(i) in correct_answers,
                )
        messages.success(self.request, 'Question updated successfully.')
        return redirect('quizzes:quiz_detail', pk=question.quiz_id)


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class QuestionDeleteView(DeleteView):
    model = QuizQuestion

    def delete(self, request, *args, **kwargs):
        question = self.get_object()
        quiz_id = question.quiz_id
        question.delete()
        messages.success(request, 'Question deleted successfully.')
        return redirect('quizzes:quiz_detail', pk=quiz_id)


def load_quizzes(request):
    class_id = request.GET.get('class_id')
    if class_id:
        quizzes = Quiz.objects.filter(class_meta_id=class_id, is_published=True).order_by('-due_date')
    else:
        quizzes = Quiz.objects.none()
    return render(request, 'quizzes/partials/quiz_options.html', {'quizzes': quizzes})
