from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, View
from django.http import JsonResponse, HttpResponseRedirect, Http404
from django.db.models import Count, Q

from academics.models import Class, Enrollment
from .models import Material, MaterialComment
from .services import MaterialService, CourseProgressService


class DosenRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_dosen() and not request.user.is_admin():
            messages.error(request, 'Akses hanya untuk dosen')
            return redirect('courses:course_list')
        return super().dispatch(request, *args, **kwargs)


class MahasiswaRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        return super().dispatch(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class CourseListView(ListView):
    template_name = 'courses/course_list.html'
    context_object_name = 'enrollments'

    def get_queryset(self):
        return Enrollment.objects.filter(
            student=self.request.user,
            status='active'
        ).select_related(
            'class_enrolled', 'class_enrolled__course',
            'class_enrolled__semester', 'class_enrolled__lecturer'
        ).annotate(
            material_count=Count('class_enrolled__materials', filter=Q(class_enrolled__materials__is_published=True))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_enrolled'] = self.get_queryset().count()
        return context


@method_decorator(login_required, name='dispatch')
class CourseDetailView(DetailView):
    template_name = 'courses/course_detail.html'
    context_object_name = 'class_obj'

    def get_object(self, queryset=None):
        return get_object_or_404(
            Class.objects.select_related('course', 'semester', 'lecturer'),
            pk=self.kwargs['pk']
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        class_obj = context['class_obj']
        is_enrolled = Enrollment.objects.filter(
            student=self.request.user,
            class_enrolled=class_obj,
            status='active'
        ).exists()
        context['is_enrolled'] = is_enrolled

        if is_enrolled:
            materials = Material.objects.filter(
                class_meta=class_obj, is_published=True
            ).order_by('order', '-created_at')
            context['materials'] = materials
            progress_service = CourseProgressService()
            context['progress'] = progress_service.get_completion_stats(
                self.request.user.id, class_obj.id
            )
            completed_ids = CourseProgressService().progress_repo.get_for_student(
                self.request.user.id, class_obj.id
            ).filter(is_completed=True).values_list('material_id', flat=True)
            context['completed_materials'] = set(completed_ids)
        else:
            context['materials'] = []
            context['progress'] = {'total': 0, 'completed': 0, 'percentage': 0}
            context['completed_materials'] = set()
        return context


@method_decorator(login_required, name='dispatch')
class MaterialListView(ListView):
    template_name = 'courses/material_list.html'
    context_object_name = 'materials'
    paginate_by = 20

    def get_queryset(self):
        class_id = self.kwargs['class_id']
        qs = Material.objects.filter(class_meta_id=class_id).order_by('order', '-created_at')
        if self.request.user.is_mahasiswa():
            qs = qs.filter(is_published=True)
        return qs.select_related('uploaded_by')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['class_obj'] = get_object_or_404(
            Class.objects.select_related('course', 'semester'),
            pk=self.kwargs['class_id']
        )
        return context


@method_decorator(login_required, name='dispatch')
class MaterialDetailView(DetailView):
    model = Material
    template_name = 'courses/material_detail.html'
    context_object_name = 'material'

    def get_object(self, queryset=None):
        obj = get_object_or_404(
            Material.objects.select_related('class_meta', 'class_meta__course', 'class_meta__lecturer', 'uploaded_by'),
            pk=self.kwargs['pk']
        )
        if self.request.user.is_mahasiswa() and not obj.is_published:
            raise Http404('Material tidak ditemukan')
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        material = context['material']
        context['comments'] = MaterialComment.objects.filter(
            material=material
        ).select_related('user').order_by('created_at')

        if self.request.user.is_authenticated:
            progress_service = CourseProgressService()
            context['is_completed'] = progress_service.progress_repo.is_completed(
                self.request.user.id, material.id
            )
        return context


@method_decorator(login_required, name='dispatch')
class MyCoursesView(DosenRequiredMixin, ListView):
    template_name = 'courses/my_courses.html'
    context_object_name = 'classes'

    def get_queryset(self):
        return Class.objects.filter(
            Q(lecturer=self.request.user) | Q(co_lecturer=self.request.user)
        ).select_related(
            'course', 'semester'
        ).annotate(
            material_count=Count('materials'),
            student_count=Count('enrollments', filter=Q(enrollments__status='active'))
        ).order_by('-semester__start_date', 'course__code')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        classes = context['classes']
        for c in classes:
            c.published_count = Material.objects.filter(
                class_meta=c, is_published=True
            ).count()
        context['total_classes'] = classes.count()
        return context


@method_decorator(login_required, name='dispatch')
class MaterialManageView(DosenRequiredMixin, ListView):
    template_name = 'courses/material_list.html'
    context_object_name = 'materials'

    def get_queryset(self):
        class_id = self.kwargs['class_id']
        return Material.objects.filter(class_meta_id=class_id).order_by(
            'order', '-created_at'
        ).select_related('uploaded_by')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['class_obj'] = get_object_or_404(
            Class.objects.select_related('course', 'semester'),
            pk=self.kwargs['class_id']
        )
        context['is_dosen_view'] = True
        context['total_materials'] = self.get_queryset().count()
        return context


@method_decorator(login_required, name='dispatch')
class MaterialUploadView(DosenRequiredMixin, CreateView):
    model = Material
    template_name = 'courses/material_form.html'
    fields = ['title', 'description', 'file_type', 'file', 'file_url', 'is_published', 'allow_download', 'order']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['class_obj'] = get_object_or_404(
            Class.objects.select_related('course', 'semester'),
            pk=self.kwargs['class_id']
        )
        return context

    def form_valid(self, form):
        form.instance.class_meta_id = self.kwargs['class_id']
        form.instance.uploaded_by = self.request.user

        service = MaterialService()
        data = {
            'title': form.cleaned_data['title'],
            'description': form.cleaned_data.get('description', ''),
            'file_type': form.cleaned_data.get('file_type', 'other'),
            'file': form.cleaned_data.get('file'),
            'file_url': form.cleaned_data.get('file_url', ''),
            'is_published': form.cleaned_data.get('is_published', True),
            'allow_download': form.cleaned_data.get('allow_download', True),
            'order': form.cleaned_data.get('order', 0),
        }
        result = service.upload_material(self.kwargs['class_id'], self.request.user.id, **data)
        if result['success']:
            messages.success(self.request, 'Material berhasil diupload')
            return redirect('courses:material_manage', class_id=self.kwargs['class_id'])
        messages.error(self.request, result['error'])
        return self.form_invalid(form)

    def get_success_url(self):
        return reverse('courses:material_manage', kwargs={'class_id': self.kwargs['class_id']})


@method_decorator(login_required, name='dispatch')
class MaterialUpdateView(DosenRequiredMixin, UpdateView):
    model = Material
    template_name = 'courses/material_form.html'
    fields = ['title', 'description', 'file_type', 'file', 'file_url', 'is_published', 'allow_download', 'order']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['class_obj'] = self.get_object().class_meta
        context['is_update'] = True
        return context

    def form_valid(self, form):
        service = MaterialService()
        data = {
            k: form.cleaned_data[k]
            for k in ['title', 'description', 'file_type', 'file', 'file_url', 'is_published', 'allow_download', 'order']
        }
        result = service.update_material(self.get_object().id, self.request.user.id, **data)
        if result['success']:
            messages.success(self.request, 'Material berhasil diperbarui')
            return redirect('courses:material_manage', class_id=self.get_object().class_meta_id)
        messages.error(self.request, result['error'])
        return self.form_invalid(form)

    def get_success_url(self):
        return reverse('courses:material_manage', kwargs={'class_id': self.get_object().class_meta_id})


@method_decorator(login_required, name='dispatch')
class MaterialDeleteView(DosenRequiredMixin, DeleteView):
    model = Material

    def post(self, request, *args, **kwargs):
        material = self.get_object()
        class_id = material.class_meta_id
        service = MaterialService()
        result = service.delete_material(material.id, request.user.id)
        if result['success']:
            messages.success(request, 'Material berhasil dihapus')
        else:
            messages.error(request, result['error'])
        return redirect('courses:material_manage', class_id=class_id)

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class MaterialTogglePublishView(DosenRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        material = get_object_or_404(Material, pk=kwargs['pk'])
        service = MaterialService()
        result = service.toggle_publish(material.id)
        if result['success']:
            messages.success(
                request,
                f"Material {'dipublikasikan' if result['is_published'] else 'disembunyikan'}"
            )
        return redirect('courses:material_manage', class_id=material.class_meta_id)

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class MarkCompleteView(View):
    def post(self, request, *args, **kwargs):
        service = CourseProgressService()
        result = service.mark_completed(
            request.user.id, kwargs['material_id'], kwargs['class_id']
        )
        if request.headers.get('HX-Request'):
            return JsonResponse({'success': result['success']})
        if result['success']:
            messages.success(request, 'Progress diperbarui')
        return redirect('courses:material_detail', pk=kwargs['material_id'])


@method_decorator(login_required, name='dispatch')
class MarkIncompleteView(View):
    def post(self, request, *args, **kwargs):
        service = CourseProgressService()
        result = service.mark_incomplete(request.user.id, kwargs['material_id'])
        if request.headers.get('HX-Request'):
            return JsonResponse({'success': result['success']})
        if result['success']:
            messages.info(request, 'Progress direset')
        return redirect('courses:material_detail', pk=kwargs['material_id'])


@method_decorator(login_required, name='dispatch')
class MaterialCommentView(View):
    def post(self, request, *args, **kwargs):
        material = get_object_or_404(Material, pk=kwargs['pk'])
        comment_text = request.POST.get('comment', '').strip()
        if not comment_text:
            messages.error(request, 'Komentar tidak boleh kosong')
            return redirect('courses:material_detail', pk=material.id)

        service = MaterialService()
        result = service.add_comment(material.id, request.user.id, comment_text)
        if result['success']:
            messages.success(request, 'Komentar ditambahkan')
        else:
            messages.error(request, result['error'])
        return redirect('courses:material_detail', pk=material.id)
