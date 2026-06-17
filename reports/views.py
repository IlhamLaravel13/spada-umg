import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, FormView, View
from .models import Report
from .services import ReportService
from .serializers import ReportSerializer


@method_decorator(login_required, name='dispatch')
class ReportListView(ListView):
    model = Report
    template_name = 'reports/report_list.html'
    context_object_name = 'reports'
    paginate_by = 20

    def get_queryset(self):
        service = ReportService()
        return service.get_reports(self.request.user)


@method_decorator(login_required, name='dispatch')
class ReportGenerateView(FormView):
    template_name = 'reports/report_form.html'
    form_class = None

    def get(self, request, *args, **kwargs):
        report_type = request.GET.get('type', 'academic')
        faculties = []
        study_programs = []
        semesters = []
        courses = []
        classes = []
        academic_years = []

        try:
            from academics.models import Faculty, StudyProgram, Semester, Course, Class as AcademicClass, AcademicYear
            faculties = Faculty.objects.filter(is_active=True)
            semesters = Semester.objects.filter(is_active=True)
            academic_years = AcademicYear.objects.all().order_by('-year')
            study_programs = StudyProgram.objects.filter(is_active=True)
            courses = Course.objects.filter(is_active=True)
            classes = AcademicClass.objects.filter(is_active=True).select_related('course', 'semester')
        except (ImportError, RuntimeError):
            pass

        context = {
            'report_type': report_type,
            'faculties': faculties,
            'study_programs': study_programs,
            'semesters': semesters,
            'courses': courses,
            'classes': classes,
            'academic_years': academic_years,
            'type_choices': Report.TYPE_CHOICES,
            'format_choices': Report.FORMAT_CHOICES,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        report_type = request.POST.get('report_type')
        fmt = request.POST.get('format', 'pdf')
        title = request.POST.get('title', '')

        parameters = {}
        for key in ['semester_id', 'class_id', 'course_id', 'faculty_id',
                     'study_program_id', 'academic_year_id', 'status',
                     'start_date', 'end_date']:
            val = request.POST.get(key)
            if val:
                parameters[key] = val

        service = ReportService()
        result = service.generate_report(
            report_type=report_type,
            fmt=fmt,
            title=title,
            parameters=parameters,
            user=request.user,
        )

        if result['success']:
            messages.success(request, 'Report is being generated.')
            return redirect('reports:detail', pk=result['report'].id)
        else:
            messages.error(request, f'Failed to generate report: {result["error"]}')
            return self.get(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class ReportDetailView(DetailView):
    model = Report
    template_name = 'reports/report_detail.html'
    context_object_name = 'report'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not obj.generated_by == self.request.user and not self.request.user.is_admin():
            raise Http404
        return obj


@method_decorator(login_required, name='dispatch')
class ReportDeleteView(View):
    def post(self, request, *args, **kwargs):
        report_id = kwargs.get('pk')
        service = ReportService()
        result = service.delete_report(report_id, request.user)
        if result['success']:
            messages.success(request, 'Report deleted.')
        else:
            messages.error(request, result['error'])
        return redirect('reports:list')


@method_decorator(login_required, name='dispatch')
class ReportDownloadView(View):
    def get(self, request, *args, **kwargs):
        report = get_object_or_404(Report, pk=kwargs.get('pk'))
        if not report.generated_by == request.user and not request.user.is_admin():
            raise Http404
        if not report.file:
            messages.error(request, 'File not available yet.')
            return redirect('reports:detail', pk=report.id)
        return redirect(report.file.url)


def api_generate_report(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    service = ReportService()
    result = service.generate_report(
        report_type=data.get('report_type', 'academic'),
        fmt=data.get('format', 'pdf'),
        title=data.get('title', ''),
        parameters={k: v for k, v in data.items() if k not in ['report_type', 'format', 'title']},
        user=request.user,
    )

    if result['success']:
        serializer = ReportSerializer(result['report'])
        return JsonResponse(serializer.data, status=201)
    return JsonResponse({'error': result['error']}, status=400)
