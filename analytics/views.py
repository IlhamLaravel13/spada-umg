from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.http import JsonResponse

from .services import AnalyticsService


class AdminRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_admin():
            from django.contrib import messages
            from django.shortcuts import redirect
            messages.error(request, 'Akses ditolak. Hanya admin yang dapat mengakses halaman ini.')
            return redirect('dashboard:redirect')
        return super().dispatch(request, *args, **kwargs)


class DosenRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_dosen() or request.user.is_admin()):
            from django.contrib import messages
            from django.shortcuts import redirect
            messages.error(request, 'Akses ditolak.')
            return redirect('dashboard:redirect')
        return super().dispatch(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class AdminDashboardView(AdminRequiredMixin, TemplateView):
    template_name = 'analytics/admin_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = AnalyticsService()
        context['overview'] = service.get_system_overview()
        context['user_stats'] = service.get_user_stats()
        context['course_stats'] = service.get_course_stats()
        return context


@method_decorator(login_required, name='dispatch')
class DosenStatsView(DosenRequiredMixin, TemplateView):
    template_name = 'analytics/dosen_stats.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = AnalyticsService()
        context['class_stats'] = service.get_dosen_stats(self.request.user)
        return context


@method_decorator(login_required, name='dispatch')
class MahasiswaStatsView(TemplateView):
    template_name = 'analytics/mahasiswa_stats.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_mahasiswa():
            service = AnalyticsService()
            context['course_stats'] = service.get_mahasiswa_stats(self.request.user)
        return context


@login_required
def get_user_stats_json(request):
    if not request.user.is_admin():
        return JsonResponse({'error': 'Forbidden'}, status=403)
    service = AnalyticsService()
    return JsonResponse(service.get_user_stats())


@login_required
def get_course_stats_json(request):
    if not request.user.is_admin():
        return JsonResponse({'error': 'Forbidden'}, status=403)
    service = AnalyticsService()
    return JsonResponse(service.get_course_stats())


@login_required
def get_attendance_rate_json(request):
    service = AnalyticsService()
    class_id = request.GET.get('class_id')
    if class_id:
        from academics.models import Class as ClassModel
        class_obj = ClassModel.objects.filter(id=class_id).first()
        if class_obj:
            return JsonResponse(service.get_attendance_rate(class_obj))
    return JsonResponse(service.get_attendance_rate())
