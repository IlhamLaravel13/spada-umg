from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.db.models import Q

from .models import Faculty, StudyProgram, AcademicYear, Semester, Course, Class, Enrollment
from .services import (
    FacultyService, StudyProgramService, CourseService, ClassService,
    EnrollmentService, SemesterService, AcademicYearService,
)
from .repositories import FacultyRepository


def is_admin_or_dosen(user):
    return user.is_authenticated and (user.is_admin() or user.is_dosen())


class HTMXMixin:
    def htmx_render(self, template, context):
        if self.request.headers.get('HX-Request'):
            return render(self.request, template, context)
        return render(self.request, template, context)


class FacultyListView(HTMXMixin, ListView):
    model = Faculty
    template_name = 'academics/faculty_list.html'
    context_object_name = 'faculties'
    paginate_by = 20

    def get_queryset(self):
        qs = FacultyService().get_active() if not self.request.user.is_staff else FacultyService().get_all()
        query = self.request.GET.get('q')
        if query:
            qs = qs.filter(
                Q(name__icontains=query) | Q(code__icontains=query)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_count'] = FacultyRepository().count()
        context['active_count'] = FacultyRepository().get_active().count()
        return context


class FacultyDetailView(DetailView):
    model = Faculty
    template_name = 'academics/faculty_detail.html'
    context_object_name = 'faculty'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['study_programs'] = self.object.study_programs.filter(is_active=True)
        context['courses'] = Course.objects.filter(
            study_program__faculty=self.object, is_active=True
        )[:10]
        return context


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class FacultyCreateView(CreateView):
    model = Faculty
    template_name = 'academics/faculty_form.html'
    fields = ['name', 'code', 'description', 'dean', 'logo', 'is_active']
    success_url = reverse_lazy('academics:faculty_list')

    def form_valid(self, form):
        result = FacultyService().create(**form.cleaned_data)
        if result['success']:
            messages.success(self.request, 'Faculty created successfully.')
            if self.request.headers.get('HX-Request'):
                return HttpResponse(status=201, headers={'HX-Trigger': 'facultyListChanged'})
            return redirect(self.success_url)
        messages.error(self.request, result['error'])
        return self.form_invalid(form)

    def form_invalid(self, form):
        if self.request.headers.get('HX-Request'):
            html = render_to_string(self.template_name, {'form': form, 'object': None}, request=self.request)
            return HttpResponse(html, status=422)
        return super().form_invalid(form)


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class FacultyUpdateView(UpdateView):
    model = Faculty
    template_name = 'academics/faculty_form.html'
    fields = ['name', 'code', 'description', 'dean', 'logo', 'is_active']
    success_url = reverse_lazy('academics:faculty_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        return context

    def form_valid(self, form):
        result = FacultyService().update(self.get_object().id, **form.cleaned_data)
        if result['success']:
            messages.success(self.request, 'Faculty updated successfully.')
            if self.request.headers.get('HX-Request'):
                return HttpResponse(status=200, headers={'HX-Trigger': 'facultyListChanged'})
            return redirect(self.success_url)
        messages.error(self.request, result['error'])
        return self.form_invalid(form)

    def form_invalid(self, form):
        if self.request.headers.get('HX-Request'):
            html = render_to_string(self.template_name, {'form': form, 'object': self.get_object(), 'is_update': True}, request=self.request)
            return HttpResponse(html, status=422)
        return super().form_invalid(form)


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class FacultyDeleteView(DeleteView):
    model = Faculty
    success_url = reverse_lazy('academics:faculty_list')

    def delete(self, request, *args, **kwargs):
        result = FacultyService().delete(kwargs.get('pk'))
        if result['success']:
            messages.success(request, result['message'])
        else:
            messages.error(request, result['error'])
        if request.headers.get('HX-Request'):
            return HttpResponse(status=200, headers={'HX-Trigger': 'facultyListChanged'})
        return redirect(self.success_url)


class StudyProgramListView(ListView):
    model = StudyProgram
    template_name = 'academics/studyprogram_list.html'
    context_object_name = 'study_programs'
    paginate_by = 20

    def get_queryset(self):
        qs = StudyProgramService().get_all()
        query = self.request.GET.get('q')
        faculty_id = self.request.GET.get('faculty')
        if query:
            qs = qs.filter(Q(name__icontains=query) | Q(code__icontains=query))
        if faculty_id:
            qs = qs.filter(faculty_id=faculty_id)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['faculties'] = FacultyRepository().get_active()
        return context


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class StudyProgramCreateView(CreateView):
    model = StudyProgram
    template_name = 'academics/studyprogram_form.html'
    fields = ['faculty', 'name', 'code', 'degree', 'description', 'head', 'is_active']
    success_url = reverse_lazy('academics:studyprogram_list')

    def form_valid(self, form):
        result = StudyProgramService().create(**form.cleaned_data)
        if result['success']:
            messages.success(self.request, 'Study Program created successfully.')
            return redirect(self.success_url)
        messages.error(self.request, result['error'])
        return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['faculties'] = FacultyRepository().get_active()
        return context


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class StudyProgramUpdateView(UpdateView):
    model = StudyProgram
    template_name = 'academics/studyprogram_form.html'
    fields = ['faculty', 'name', 'code', 'degree', 'description', 'head', 'is_active']
    success_url = reverse_lazy('academics:studyprogram_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        context['faculties'] = FacultyRepository().get_active()
        return context

    def form_valid(self, form):
        result = StudyProgramService().update(self.get_object().id, **form.cleaned_data)
        if result['success']:
            messages.success(self.request, 'Study Program updated successfully.')
            return redirect(self.success_url)
        messages.error(self.request, result['error'])
        return self.form_invalid(form)


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class StudyProgramDeleteView(DeleteView):
    model = StudyProgram
    success_url = reverse_lazy('academics:studyprogram_list')

    def delete(self, request, *args, **kwargs):
        result = StudyProgramService().delete(kwargs.get('pk'))
        if result['success']:
            messages.success(request, result['message'])
        else:
            messages.error(request, result['error'])
        return redirect(self.success_url)


class CourseListView(ListView):
    model = Course
    template_name = 'academics/course_list.html'
    context_object_name = 'courses'
    paginate_by = 20

    def get_queryset(self):
        qs = CourseService().get_all()
        query = self.request.GET.get('q')
        sp_id = self.request.GET.get('study_program')
        faculty_id = self.request.GET.get('faculty')
        if query:
            qs = qs.filter(Q(code__icontains=query) | Q(name__icontains=query))
        if sp_id:
            qs = qs.filter(study_program_id=sp_id)
        if faculty_id:
            qs = qs.filter(study_program__faculty_id=faculty_id)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['faculties'] = FacultyRepository().get_active()
        return context


class CourseDetailView(DetailView):
    model = Course
    template_name = 'academics/course_detail.html'
    context_object_name = 'course'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['classes'] = self.object.classes.filter(is_active=True)
        return context


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class CourseCreateView(CreateView):
    model = Course
    template_name = 'academics/course_form.html'
    fields = ['study_program', 'code', 'name', 'description', 'credits', 'semester', 'is_active']
    success_url = reverse_lazy('academics:course_list')

    def form_valid(self, form):
        result = CourseService().create(**form.cleaned_data)
        if result['success']:
            messages.success(self.request, 'Course created successfully.')
            return redirect(self.success_url)
        messages.error(self.request, result['error'])
        return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['faculties'] = FacultyRepository().get_active()
        return context


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class CourseUpdateView(UpdateView):
    model = Course
    template_name = 'academics/course_form.html'
    fields = ['study_program', 'code', 'name', 'description', 'credits', 'semester', 'is_active']
    success_url = reverse_lazy('academics:course_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        context['faculties'] = FacultyRepository().get_active()
        return context

    def form_valid(self, form):
        result = CourseService().update(self.get_object().id, **form.cleaned_data)
        if result['success']:
            messages.success(self.request, 'Course updated successfully.')
            return redirect(self.success_url)
        messages.error(self.request, result['error'])
        return self.form_invalid(form)


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class CourseDeleteView(DeleteView):
    model = Course
    success_url = reverse_lazy('academics:course_list')

    def delete(self, request, *args, **kwargs):
        result = CourseService().delete(kwargs.get('pk'))
        if result['success']:
            messages.success(request, result['message'])
        else:
            messages.error(request, result['error'])
        return redirect(self.success_url)


class ClassListView(ListView):
    model = Class
    template_name = 'academics/class_list.html'
    context_object_name = 'classes'
    paginate_by = 20

    def get_queryset(self):
        qs = ClassService().get_all()
        query = self.request.GET.get('q')
        course_id = self.request.GET.get('course')
        semester_id = self.request.GET.get('semester')
        if query:
            qs = qs.filter(
                Q(code__icontains=query) | Q(name__icontains=query) |
                Q(course__name__icontains=query) | Q(course__code__icontains=query)
            )
        if course_id:
            qs = qs.filter(course_id=course_id)
        if semester_id:
            qs = qs.filter(semester_id=semester_id)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_semester'] = SemesterService().get_active()
        return context


class ClassDetailView(DetailView):
    model = Class
    template_name = 'academics/class_detail.html'
    context_object_name = 'class_obj'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['enrollments'] = self.object.enrollments.select_related('student').all()
        context['enrolled_count'] = self.object.enrollments.filter(status='active').count()
        return context


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class ClassCreateView(CreateView):
    model = Class
    template_name = 'academics/class_form.html'
    fields = ['course', 'semester', 'name', 'code', 'lecturer', 'co_lecturer',
              'class_type', 'room', 'schedule', 'max_students', 'meeting_link', 'description', 'is_active']
    success_url = reverse_lazy('academics:class_list')

    def form_valid(self, form):
        result = ClassService().create(**form.cleaned_data)
        if result['success']:
            messages.success(self.request, 'Class created successfully.')
            return redirect(self.success_url)
        messages.error(self.request, result['error'])
        return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_semester'] = SemesterService().get_active()
        return context


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class ClassUpdateView(UpdateView):
    model = Class
    template_name = 'academics/class_form.html'
    fields = ['course', 'semester', 'name', 'code', 'lecturer', 'co_lecturer',
              'class_type', 'room', 'schedule', 'max_students', 'meeting_link', 'description', 'is_active']
    success_url = reverse_lazy('academics:class_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        return context

    def form_valid(self, form):
        result = ClassService().update(self.get_object().id, **form.cleaned_data)
        if result['success']:
            messages.success(self.request, 'Class updated successfully.')
            return redirect(self.success_url)
        messages.error(self.request, result['error'])
        return self.form_invalid(form)


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class ClassDeleteView(DeleteView):
    model = Class
    success_url = reverse_lazy('academics:class_list')

    def delete(self, request, *args, **kwargs):
        result = ClassService().delete(kwargs.get('pk'))
        if result['success']:
            messages.success(request, result['message'])
        else:
            messages.error(request, result['error'])
        return redirect(self.success_url)


class SemesterListView(ListView):
    model = Semester
    template_name = 'academics/semester_list.html'
    context_object_name = 'semesters'
    paginate_by = 20

    def get_queryset(self):
        qs = SemesterService().get_all()
        ay_id = self.request.GET.get('academic_year')
        if ay_id:
            qs = qs.filter(academic_year_id=ay_id)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['academic_years'] = AcademicYearService().get_all()
        return context


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class SemesterCreateView(CreateView):
    model = Semester
    template_name = 'academics/semester_form.html'
    fields = ['academic_year', 'name', 'code', 'start_date', 'end_date',
              'midterm_start', 'midterm_end', 'finalterm_start', 'finalterm_end',
              'enrollment_start', 'enrollment_end', 'is_active']
    success_url = reverse_lazy('academics:semester_list')

    def form_valid(self, form):
        result = SemesterService().create(**form.cleaned_data)
        if result['success']:
            messages.success(self.request, 'Semester created successfully.')
            return redirect(self.success_url)
        messages.error(self.request, result['error'])
        return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['academic_years'] = AcademicYearService().get_all()
        return context


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class SemesterUpdateView(UpdateView):
    model = Semester
    template_name = 'academics/semester_form.html'
    fields = ['academic_year', 'name', 'code', 'start_date', 'end_date',
              'midterm_start', 'midterm_end', 'finalterm_start', 'finalterm_end',
              'enrollment_start', 'enrollment_end', 'is_active']
    success_url = reverse_lazy('academics:semester_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        context['academic_years'] = AcademicYearService().get_all()
        return context

    def form_valid(self, form):
        result = SemesterService().update(self.get_object().id, **form.cleaned_data)
        if result['success']:
            messages.success(self.request, 'Semester updated successfully.')
            return redirect(self.success_url)
        messages.error(self.request, result['error'])
        return self.form_invalid(form)


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class SemesterDeleteView(DeleteView):
    model = Semester
    success_url = reverse_lazy('academics:semester_list')

    def delete(self, request, *args, **kwargs):
        result = SemesterService().delete(kwargs.get('pk'))
        if result['success']:
            messages.success(request, result['message'])
        else:
            messages.error(request, result['error'])
        return redirect(self.success_url)


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class SemesterActivateView(TemplateView):
    def post(self, request, *args, **kwargs):
        semester_id = kwargs.get('pk')
        result = SemesterService().activate(semester_id)
        if result['success']:
            messages.success(request, result.get('message', 'Semester activated successfully.'))
        else:
            messages.error(request, result['error'])
        return redirect('academics:semester_list')


class AcademicYearListView(ListView):
    model = AcademicYear
    template_name = 'academics/academic_year_list.html'
    context_object_name = 'academic_years'

    def get_queryset(self):
        qs = AcademicYearService().get_all()
        query = self.request.GET.get('q')
        if query:
            qs = qs.filter(year__icontains=query)
        return qs


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class AcademicYearCreateView(CreateView):
    model = AcademicYear
    template_name = 'academics/academic_year_form.html'
    fields = ['year', 'start_date', 'end_date', 'is_even_semester', 'description', 'is_active']
    success_url = reverse_lazy('academics:academic_year_list')

    def form_valid(self, form):
        result = AcademicYearService().create(**form.cleaned_data)
        if result['success']:
            messages.success(self.request, 'Academic Year created successfully.')
            return redirect(self.success_url)
        messages.error(self.request, result['error'])
        return self.form_invalid(form)


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class AcademicYearUpdateView(UpdateView):
    model = AcademicYear
    template_name = 'academics/academic_year_form.html'
    fields = ['year', 'start_date', 'end_date', 'is_even_semester', 'description', 'is_active']
    success_url = reverse_lazy('academics:academic_year_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        return context

    def form_valid(self, form):
        result = AcademicYearService().update(self.get_object().id, **form.cleaned_data)
        if result['success']:
            messages.success(self.request, 'Academic Year updated successfully.')
            return redirect(self.success_url)
        messages.error(self.request, result['error'])
        return self.form_invalid(form)


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class AcademicYearDeleteView(DeleteView):
    model = AcademicYear
    success_url = reverse_lazy('academics:academic_year_list')

    def delete(self, request, *args, **kwargs):
        result = AcademicYearService().delete(kwargs.get('pk'))
        if result['success']:
            messages.success(request, result['message'])
        else:
            messages.error(request, result['error'])
        return redirect(self.success_url)


class EnrollmentListView(ListView):
    model = Enrollment
    template_name = 'academics/enrollment_list.html'
    context_object_name = 'enrollments'
    paginate_by = 50

    def get_queryset(self):
        qs = EnrollmentService().get_all()
        class_id = self.request.GET.get('class')
        student_query = self.request.GET.get('q')
        status = self.request.GET.get('status')
        if class_id:
            qs = qs.filter(class_enrolled_id=class_id)
        if student_query:
            qs = qs.filter(
                Q(student__username__icontains=student_query) |
                Q(student__nim__icontains=student_query) |
                Q(student__first_name__icontains=student_query) |
                Q(student__last_name__icontains=student_query)
            )
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_semester'] = SemesterService().get_active()
        return context


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class EnrollmentCreateView(CreateView):
    model = Enrollment
    template_name = 'academics/enrollment_form.html'
    fields = ['student', 'class_enrolled', 'status']
    success_url = reverse_lazy('academics:enrollment_list')

    def form_valid(self, form):
        result = EnrollmentService().enroll_student(
            form.cleaned_data['student'].id,
            form.cleaned_data['class_enrolled'].id,
        )
        if result['success']:
            messages.success(self.request, 'Student enrolled successfully.')
            return redirect(self.success_url)
        messages.error(self.request, result['error'])
        return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_semester'] = SemesterService().get_active()
        return context


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class EnrollmentUpdateView(UpdateView):
    model = Enrollment
    template_name = 'academics/enrollment_form.html'
    fields = ['status', 'grade_final', 'grade_letter']
    success_url = reverse_lazy('academics:enrollment_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        return context

    def form_valid(self, form):
        enrollment = self.get_object()
        result = EnrollmentService().update_grade(
            enrollment.id,
            grade_final=form.cleaned_data.get('grade_final'),
            grade_letter=form.cleaned_data.get('grade_letter', ''),
        )
        if result['success']:
            if form.cleaned_data.get('status') != enrollment.status:
                EnrollmentService().enrollment_repo.update(enrollment.id, status=form.cleaned_data['status'])
            messages.success(self.request, 'Enrollment updated successfully.')
            return redirect(self.success_url)
        messages.error(self.request, result['error'])
        return self.form_invalid(form)


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class EnrollmentDeleteView(DeleteView):
    model = Enrollment
    success_url = reverse_lazy('academics:enrollment_list')

    def delete(self, request, *args, **kwargs):
        result = EnrollmentService().withdraw_student(kwargs.get('pk'))
        if result['success']:
            messages.success(request, result['message'])
        else:
            messages.error(request, result['error'])
        return redirect(self.success_url)


def load_study_programs(request):
    faculty_id = request.GET.get('faculty_id')
    if faculty_id:
        sps = StudyProgram.objects.filter(faculty_id=faculty_id, is_active=True).order_by('name')
    else:
        sps = StudyProgram.objects.none()
    return render(request, 'academics/partials/study_program_options.html', {'study_programs': sps})


def load_courses(request):
    sp_id = request.GET.get('study_program_id')
    if sp_id:
        courses = Course.objects.filter(study_program_id=sp_id, is_active=True).order_by('code')
    else:
        courses = Course.objects.none()
    return render(request, 'academics/partials/course_options.html', {'courses': courses})
