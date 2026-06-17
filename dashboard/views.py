from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from analytics.services import AnalyticsService
from academics.repositories import EnrollmentRepository, ClassRepository
from assignments.repositories import AssignmentRepository

class DashboardRedirectView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        if request.user.role == 'superadmin' or request.user.role == 'admin':
            return redirect('dashboard:admin')
        elif request.user.role == 'dosen':
            return redirect('dashboard:dosen')
        else:
            return redirect('dashboard:mahasiswa')

@method_decorator(staff_member_required, name='dispatch')
class AdminDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/admin/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        analytics = AnalyticsService()
        context['total_users'] = analytics.get_total_users()
        context['total_dosen'] = analytics.get_total_dosen()
        context['total_mahasiswa'] = analytics.get_total_mahasiswa()
        context['total_courses'] = analytics.get_total_courses()
        context['total_classes'] = analytics.get_total_classes()
        context['recent_users'] = analytics.get_recent_users()
        context['recent_activities'] = analytics.get_recent_activities()
        context['stats_by_role'] = analytics.get_user_stats_by_role()
        context['enrollment_stats'] = analytics.get_enrollment_stats()
        return context

@method_decorator(login_required, name='dispatch')
class DosenDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/dosen/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        analytics = AnalyticsService()
        context['my_classes'] = ClassRepository().get_by_lecturer(self.request.user.id)
        context['total_classes'] = len(context['my_classes'])
        context['total_students'] = analytics.get_lecturer_total_students(self.request.user)
        context['pending_assignments'] = AssignmentRepository().get_all().filter(
            class_meta__lecturer=self.request.user,
            due_date__gte=timezone.now()
        ).count()
        context['recent_attendance'] = analytics.get_lecturer_recent_attendance(self.request.user)
        context['attendance_rate'] = analytics.get_lecturer_attendance_rate(self.request.user)
        return context

@method_decorator(login_required, name='dispatch')
class MahasiswaDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/mahasiswa/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        analytics = AnalyticsService()
        context['enrolled_classes'] = EnrollmentRepository().get_by_student(self.request.user.id)
        context['total_classes'] = len(context['enrolled_classes'])
        context['pending_tasks'] = AssignmentRepository().get_all().filter(
            class_meta__enrollments__student=self.request.user,
            due_date__gte=timezone.now()
        ).distinct().count()
        context['upcoming_quizzes'] = analytics.get_student_upcoming_quizzes(self.request.user)
        context['recent_grades'] = analytics.get_student_recent_grades(self.request.user)
        context['attendance_rate'] = analytics.get_student_attendance_rate(self.request.user)
        context['overall_grade'] = analytics.get_student_overall_grade(self.request.user)
        return context
