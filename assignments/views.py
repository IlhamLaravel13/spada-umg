from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.db.models import Q
from django.utils import timezone

from .models import Assignment, AssignmentSubmission, AssignmentSubmissionAttachment
from .services import AssignmentService, AssignmentSubmissionService
from .repositories import AssignmentRepository


def is_admin_or_dosen(user):
    return user.is_authenticated and (user.is_admin() or user.is_dosen())


def is_mahasiswa(user):
    return user.is_authenticated and user.is_mahasiswa()


class HTMXMixin:
    def htmx_render(self, template, context):
        if self.request.headers.get('HX-Request'):
            return render(self.request, template, context)
        return render(self.request, template, context)


class AssignmentListView(HTMXMixin, ListView):
    model = Assignment
    template_name = 'assignments/assignment_list.html'
    context_object_name = 'assignments'
    paginate_by = 20

    def get_queryset(self):
        service = AssignmentService()
        user = self.request.user
        class_id = self.request.GET.get('class_id')
        status = self.request.GET.get('status')

        if user.is_authenticated and user.is_dosen():
            qs = Assignment.objects.filter(class_meta__lecturer=user)
        elif user.is_authenticated and user.is_mahasiswa():
            enrolled_classes = user.enrollments.filter(status='active').values_list('class_enrolled_id', flat=True)
            qs = Assignment.objects.filter(class_meta_id__in=enrolled_classes, is_published=True)
        else:
            qs = service.get_all()

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
        context['total_count'] = self.get_queryset().count()
        context['class_id'] = self.request.GET.get('class_id')
        return context


class AssignmentDetailView(DetailView):
    model = Assignment
    template_name = 'assignments/assignment_detail.html'
    context_object_name = 'assignment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        assignment = self.object

        if user.is_authenticated:
            context['user_submissions'] = AssignmentSubmission.objects.filter(
                student=user, assignment=assignment
            ).order_by('-attempt_number')

            if user.is_dosen() or user.is_admin():
                context['all_submissions'] = AssignmentSubmission.objects.filter(
                    assignment=assignment
                ).select_related('student').order_by('-submitted_at')

            context['can_submit'] = (
                user.is_mahasiswa() and
                assignment.is_published and
                (assignment.allow_late_submission or not assignment.is_past_due())
            )

        return context


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class AssignmentCreateView(CreateView):
    model = Assignment
    template_name = 'assignments/assignment_form.html'
    fields = [
        'class_meta', 'title', 'description', 'instructions', 'max_score', 'passing_score',
        'due_date', 'allow_late_submission', 'late_penalty_percent', 'max_attempts',
        'is_published', 'is_group_assignment', 'file_required', 'allowed_file_types',
    ]
    success_url = reverse_lazy('assignments:assignment_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        result = AssignmentService().create(**form.cleaned_data, created_by=self.request.user)
        if result['success']:
            messages.success(self.request, 'Assignment created successfully.')
            if self.request.headers.get('HX-Request'):
                return HttpResponse(status=201, headers={'HX-Trigger': 'assignmentListChanged'})
            return redirect(self.success_url)
        messages.error(self.request, result['error'])
        return self.form_invalid(form)

    def form_invalid(self, form):
        if self.request.headers.get('HX-Request'):
            html = render_to_string(self.template_name, {'form': form, 'object': None}, request=self.request)
            return HttpResponse(html, status=422)
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['class_id'] = self.request.GET.get('class_id')
        return context


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class AssignmentUpdateView(UpdateView):
    model = Assignment
    template_name = 'assignments/assignment_form.html'
    fields = [
        'class_meta', 'title', 'description', 'instructions', 'max_score', 'passing_score',
        'due_date', 'allow_late_submission', 'late_penalty_percent', 'max_attempts',
        'is_published', 'is_group_assignment', 'file_required', 'allowed_file_types',
    ]
    success_url = reverse_lazy('assignments:assignment_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        return context

    def form_valid(self, form):
        result = AssignmentService().update(self.get_object().id, **form.cleaned_data)
        if result['success']:
            messages.success(self.request, 'Assignment updated successfully.')
            if self.request.headers.get('HX-Request'):
                return HttpResponse(status=200, headers={'HX-Trigger': 'assignmentListChanged'})
            return redirect(self.success_url)
        messages.error(self.request, result['error'])
        return self.form_invalid(form)

    def form_invalid(self, form):
        if self.request.headers.get('HX-Request'):
            html = render_to_string(self.template_name, {'form': form, 'object': self.get_object(), 'is_update': True}, request=self.request)
            return HttpResponse(html, status=422)
        return super().form_invalid(form)


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class AssignmentDeleteView(DeleteView):
    model = Assignment
    success_url = reverse_lazy('assignments:assignment_list')

    def delete(self, request, *args, **kwargs):
        result = AssignmentService().delete(kwargs.get('pk'))
        if result['success']:
            messages.success(request, result['message'])
        else:
            messages.error(request, result['error'])
        if request.headers.get('HX-Request'):
            return HttpResponse(status=200, headers={'HX-Trigger': 'assignmentListChanged'})
        return redirect(self.success_url)


@method_decorator([login_required, user_passes_test(is_mahasiswa)], name='dispatch')
class AssignmentSubmitView(CreateView):
    model = AssignmentSubmission
    template_name = 'assignments/assignment_submit.html'
    fields = ['notes']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['assignment'] = get_object_or_404(Assignment, pk=self.kwargs.get('pk'))
        return context

    def form_valid(self, form):
        assignment = get_object_or_404(Assignment, pk=self.kwargs.get('pk'))
        service = AssignmentSubmissionService()
        file = self.request.FILES.get('file')
        result = service.submit(
            student_id=self.request.user.id,
            assignment_id=assignment.id,
            file=file,
            notes=form.cleaned_data.get('notes', ''),
        )
        if result['success']:
            messages.success(self.request, 'Assignment submitted successfully.')
            return redirect('assignments:assignment_detail', pk=assignment.pk)
        messages.error(self.request, result['error'])
        return self.form_invalid(form)


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class AssignmentGradeView(UpdateView):
    model = AssignmentSubmission
    template_name = 'assignments/assignment_grade.html'
    fields = ['score', 'feedback']
    pk_url_kwarg = 'submission_pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['assignment'] = self.get_object().assignment
        return context

    def form_valid(self, form):
        submission = self.get_object()
        service = AssignmentSubmissionService()
        result = service.grade(
            submission_id=submission.id,
            score=form.cleaned_data.get('score'),
            feedback=form.cleaned_data.get('feedback', ''),
            graded_by_id=self.request.user.id,
        )
        if result['success']:
            messages.success(self.request, 'Submission graded successfully.')
            return redirect('assignments:assignment_detail', pk=submission.assignment_id)
        messages.error(self.request, result['error'])
        return self.form_invalid(form)


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class SubmissionListView(ListView):
    model = AssignmentSubmission
    template_name = 'assignments/submission_list.html'
    context_object_name = 'submissions'
    paginate_by = 20

    def get_queryset(self):
        qs = AssignmentSubmission.objects.select_related('student', 'assignment', 'graded_by').all()
        assignment_id = self.request.GET.get('assignment_id')
        student_query = self.request.GET.get('q')
        status = self.request.GET.get('status')

        if assignment_id:
            qs = qs.filter(assignment_id=assignment_id)
        if student_query:
            qs = qs.filter(
                Q(student__username__icontains=student_query) |
                Q(student__nim__icontains=student_query) |
                Q(student__first_name__icontains=student_query)
            )
        if status:
            qs = qs.filter(status=status)

        user = self.request.user
        if user.is_dosen():
            qs = qs.filter(assignment__class_meta__lecturer=user)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['assignment_id'] = self.request.GET.get('assignment_id')
        context['status_filter'] = self.request.GET.get('status')
        return context


def load_assignments(request):
    class_id = request.GET.get('class_id')
    if class_id:
        assignments = Assignment.objects.filter(class_meta_id=class_id, is_published=True).order_by('-due_date')
    else:
        assignments = Assignment.objects.none()
    return render(request, 'assignments/partials/assignment_options.html', {'assignments': assignments})
