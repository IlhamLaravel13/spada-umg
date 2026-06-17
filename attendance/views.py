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

from .models import AttendanceSession, Attendance
from .services import AttendanceService
from .repositories import AttendanceSessionRepository, AttendanceRepository
from academics.models import Class as ClassModel
from academics.repositories import ClassRepository


def is_dosen_or_admin(user):
    return user.is_authenticated and (user.is_dosen() or user.is_admin())

def is_mahasiswa(user):
    return user.is_authenticated and user.is_mahasiswa()


class HTMXMixin:
    def htmx_render(self, template, context):
        if self.request.headers.get('HX-Request'):
            return render(self.request, template, context)
        return render(self.request, template, context)


class SessionListView(HTMXMixin, ListView):
    model = AttendanceSession
    template_name = 'attendance/session_list.html'
    context_object_name = 'sessions'
    paginate_by = 20

    def get_queryset(self):
        service = AttendanceService()
        class_id = self.request.GET.get('class_id')
        qs = service.get_all_sessions()
        if class_id:
            qs = qs.filter(class_meta_id=class_id)
        elif self.request.user.is_dosen():
            qs = qs.filter(class_meta__lecturer=self.request.user)
        elif self.request.user.is_mahasiswa():
            qs = qs.filter(class_meta__enrollments__student=self.request.user)
        query = self.request.GET.get('q')
        if query:
            qs = qs.filter(
                Q(title__icontains=query) | Q(topic__icontains=query) |
                Q(class_meta__course__name__icontains=query)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['class_id'] = self.request.GET.get('class_id')
        return context


class SessionDetailView(DetailView):
    model = AttendanceSession
    template_name = 'attendance/session_detail.html'
    context_object_name = 'session'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = AttendanceService()
        context['attendances'] = service.get_attendances_for_session(self.object.id)
        context['total_students'] = self.object.class_meta.enrollments.filter(status='active').count()
        context['present_count'] = context['attendances'].filter(status='present').count()
        return context


@method_decorator([login_required, user_passes_test(is_dosen_or_admin)], name='dispatch')
class SessionCreateView(CreateView):
    model = AttendanceSession
    template_name = 'attendance/session_form.html'
    fields = ['class_meta', 'title', 'date', 'start_time', 'end_time', 'topic', 'meeting_number', 'is_active']
    success_url = reverse_lazy('attendance:session_list')

    def get_initial(self):
        initial = super().get_initial()
        class_id = self.request.GET.get('class_id')
        if class_id:
            initial['class_meta'] = class_id
        return initial

    def form_valid(self, form):
        service = AttendanceService()
        result = service.create_session(
            class_meta_id=form.cleaned_data['class_meta'].id,
            title=form.cleaned_data['title'],
            date=form.cleaned_data['date'],
            start_time=form.cleaned_data['start_time'],
            end_time=form.cleaned_data['end_time'],
            topic=form.cleaned_data.get('topic', ''),
            meeting_number=form.cleaned_data.get('meeting_number', 1),
            is_active=form.cleaned_data.get('is_active', True),
            created_by=self.request.user,
        )
        if result['success']:
            messages.success(self.request, 'Sesi absensi berhasil dibuat.')
            if self.request.headers.get('HX-Request'):
                return HttpResponse(status=201, headers={'HX-Trigger': 'sessionListChanged'})
            return redirect(self.success_url)
        messages.error(self.request, result['error'])
        return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['class_repo'] = ClassRepository()
        context['today'] = timezone.now().date()
        return context

    def form_invalid(self, form):
        if self.request.headers.get('HX-Request'):
            html = render_to_string(self.template_name, {'form': form, 'object': None}, request=self.request)
            return HttpResponse(html, status=422)
        return super().form_invalid(form)


@method_decorator([login_required, user_passes_test(is_dosen_or_admin)], name='dispatch')
class SessionUpdateView(UpdateView):
    model = AttendanceSession
    template_name = 'attendance/session_form.html'
    fields = ['class_meta', 'title', 'date', 'start_time', 'end_time', 'topic', 'meeting_number', 'is_active']
    success_url = reverse_lazy('attendance:session_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        return context

    def form_valid(self, form):
        service = AttendanceService()
        result = service.update_session(
            self.get_object().id,
            class_meta_id=form.cleaned_data['class_meta'].id,
            title=form.cleaned_data['title'],
            date=form.cleaned_data['date'],
            start_time=form.cleaned_data['start_time'],
            end_time=form.cleaned_data['end_time'],
            topic=form.cleaned_data.get('topic', ''),
            meeting_number=form.cleaned_data.get('meeting_number', 1),
            is_active=form.cleaned_data.get('is_active', True),
        )
        if result['success']:
            messages.success(self.request, 'Sesi absensi berhasil diperbarui.')
            if self.request.headers.get('HX-Request'):
                return HttpResponse(status=200, headers={'HX-Trigger': 'sessionListChanged'})
            return redirect(self.success_url)
        messages.error(self.request, result['error'])
        return self.form_invalid(form)


@method_decorator([login_required, user_passes_test(is_dosen_or_admin)], name='dispatch')
class SessionDeleteView(DeleteView):
    model = AttendanceSession
    success_url = reverse_lazy('attendance:session_list')

    def delete(self, request, *args, **kwargs):
        service = AttendanceService()
        result = service.delete_session(kwargs.get('pk'))
        if result['success']:
            messages.success(request, result['message'])
        else:
            messages.error(request, result['error'])
        if request.headers.get('HX-Request'):
            return HttpResponse(status=200, headers={'HX-Trigger': 'sessionListChanged'})
        return redirect(self.success_url)


@method_decorator([login_required, user_passes_test(is_dosen_or_admin)], name='dispatch')
class SessionToggleActiveView(View):
    def post(self, request, *args, **kwargs):
        service = AttendanceService()
        session = service.get_session_by_id(kwargs.get('pk'))
        if not session:
            messages.error(request, 'Session not found')
            return redirect('attendance:session_list')
        result = service.update_session(session.id, is_active=not session.is_active)
        if result['success']:
            messages.success(request, f'Session {"activated" if not session.is_active else "deactivated"} successfully.')
        else:
            messages.error(request, result['error'])
        return redirect(request.META.get('HTTP_REFERER', 'attendance:session_list'))


@login_required
def take_attendance(request, pk):
    service = AttendanceService()
    session = service.get_session_by_id(pk)
    if not session:
        messages.error(request, 'Sesi absensi tidak ditemukan.')
        return redirect('attendance:session_list')

    if request.method == 'POST':
        qr_secret = request.POST.get('qr_secret', '')
        if qr_secret and qr_secret != session.qr_code_secret:
            messages.error(request, 'QR Code tidak valid.')
            return render(request, 'attendance/attendance_take.html', {'session': session, 'error': 'QR Code tidak valid.'})

        result = service.check_in(
            request.user,
            session.id,
            latitude=request.POST.get('latitude'),
            longitude=request.POST.get('longitude'),
            notes=request.POST.get('notes', ''),
        )
        if result['success']:
            messages.success(request, 'Absensi berhasil!')
            return redirect('attendance:my_attendance')
        messages.error(request, result['error'])
        return render(request, 'attendance/attendance_take.html', {'session': session, 'error': result['error']})

    return render(request, 'attendance/attendance_take.html', {'session': session})


@method_decorator([login_required, user_passes_test(is_dosen_or_admin)], name='dispatch')
class ManualCheckInView(View):
    def post(self, request, pk):
        service = AttendanceService()
        session = service.get_session_by_id(pk)
        if not session:
            return JsonResponse({'success': False, 'error': 'Session not found'}, status=404)

        student_id = request.POST.get('student_id')
        status = request.POST.get('status', 'present')
        notes = request.POST.get('notes', '')

        if not student_id:
            return JsonResponse({'success': False, 'error': 'Student ID required'}, status=400)

        result = service.manual_check_in(
            request.user, session.id, student_id,
            status=status, notes=notes,
        )
        if result['success']:
            if request.headers.get('HX-Request'):
                attendances = service.get_attendances_for_session(session.id)
                html = render_to_string('attendance/partials/attendance_list.html', {
                    'attendances': attendances,
                    'session': session,
                }, request=request)
                return HttpResponse(html)
            return JsonResponse({'success': True, 'data': 'Attendance recorded'})
        return JsonResponse({'success': False, 'error': result['error']}, status=400)


@method_decorator([login_required, user_passes_test(is_dosen_or_admin)], name='dispatch')
class UpdateAttendanceStatusView(View):
    def post(self, request, pk):
        service = AttendanceService()
        status = request.POST.get('status')
        if not status or status not in dict(Attendance.STATUS_CHOICES):
            return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)

        result = service.update_attendance_status(pk, status, request.user)
        if result['success']:
            if request.headers.get('HX-Request'):
                return HttpResponse(status=200, headers={'HX-Trigger': 'attendanceUpdated'})
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'error': result['error']}, status=400)


class AttendanceReportView(HTMXMixin, TemplateView):
    template_name = 'attendance/attendance_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = AttendanceService()
        class_id = self.request.GET.get('class_id')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        if class_id:
            result = service.generate_report(class_id, start_date, end_date)
            if result['success']:
                context['report'] = result['data']
                context['class_obj'] = result['data']['class']

        if self.request.user.is_dosen():
            context['classes'] = ClassModel.objects.filter(lecturer=self.request.user, is_active=True)
        elif self.request.user.is_admin():
            context['classes'] = ClassModel.objects.filter(is_active=True)
        else:
            context['classes'] = []

        context['selected_class_id'] = class_id
        context['start_date'] = start_date
        context['end_date'] = end_date
        return context


class MyAttendanceView(ListView):
    model = Attendance
    template_name = 'attendance/my_attendance.html'
    context_object_name = 'attendances'
    paginate_by = 20

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        service = AttendanceService()
        qs = service.get_my_attendances(self.request.user)
        class_id = self.request.GET.get('class_id')
        if class_id:
            qs = qs.filter(session__class_meta_id=class_id)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        enrollments = self.request.user.enrollments.filter(status='active').select_related('class_enrolled')
        context['enrolled_classes'] = [e.class_enrolled for e in enrollments]
        context['selected_class_id'] = self.request.GET.get('class_id')
        context['summary'] = {
            'total': self.get_queryset().count(),
            'present': self.get_queryset().filter(status='present').count(),
            'late': self.get_queryset().filter(status='late').count(),
            'absent': self.get_queryset().filter(status='absent').count(),
            'excused': self.get_queryset().filter(status='excused').count(),
            'sick': self.get_queryset().filter(status='sick').count(),
        }
        return context


def check_in_qr(request, session_id):
    service = AttendanceService()
    session = service.get_session_by_id(session_id)
    if not session:
        return JsonResponse({'success': False, 'error': 'Session not found'}, status=404)
    if not session.is_active:
        return JsonResponse({'success': False, 'error': 'Session is not active'}, status=400)

    result = service.check_in(request.user, session_id)
    if result['success']:
        return JsonResponse({'success': True, 'data': 'Check-in successful'})
    return JsonResponse({'success': False, 'error': result['error']}, status=400)
