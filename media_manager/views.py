from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.db.models import Q

from .models import MediaFile
from .services import MediaFileService


FILE_TYPE_CHOICES = MediaFile.FILE_TYPE_CHOICES


class MediaListView(ListView):
    model = MediaFile
    template_name = 'media_manager/media_list.html'
    context_object_name = 'media_files'
    paginate_by = 24

    def get_queryset(self):
        service = MediaFileService()
        qs = service.get_public()
        if self.request.user.is_authenticated:
            qs = service.get_all()
        query = self.request.GET.get('q')
        file_type = self.request.GET.get('type')
        if query:
            qs = qs.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(tags__icontains=query)
            )
        if file_type:
            qs = qs.filter(file_type=file_type)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['file_types'] = FILE_TYPE_CHOICES
        context['selected_type'] = self.request.GET.get('type', '')
        return context


class MediaDetailView(DetailView):
    model = MediaFile
    template_name = 'media_manager/media_detail.html'
    context_object_name = 'media_file'


@method_decorator([login_required], name='dispatch')
class MediaUploadView(CreateView):
    model = MediaFile
    template_name = 'media_manager/media_upload.html'
    fields = ['title', 'description', 'file', 'thumbnail', 'file_type', 'alt_text', 'is_public', 'tags']

    def get_success_url(self):
        return reverse('media_manager:media_detail', args=[self.object.id])

    def form_valid(self, form):
        service = MediaFileService()
        result = service.upload(**form.cleaned_data, uploaded_by=self.request.user)
        if result['success']:
            messages.success(self.request, 'File berhasil diunggah.')
            return redirect(self.get_success_url())
        messages.error(self.request, result['error'])
        return self.form_invalid(form)


@method_decorator([login_required], name='dispatch')
class MediaUpdateView(UpdateView):
    model = MediaFile
    template_name = 'media_manager/media_upload.html'
    fields = ['title', 'description', 'file', 'thumbnail', 'file_type', 'alt_text', 'is_public', 'tags']

    def get_success_url(self):
        return reverse('media_manager:media_detail', args=[self.object.id])

    def get_queryset(self):
        if self.request.user.is_admin():
            return MediaFile.objects.all()
        return MediaFile.objects.filter(uploaded_by=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        return context

    def form_valid(self, form):
        service = MediaFileService()
        result = service.update(self.object.id, **form.cleaned_data)
        if result['success']:
            messages.success(self.request, 'File berhasil diperbarui.')
            return redirect(self.get_success_url())
        messages.error(self.request, result['error'])
        return self.form_invalid(form)


@method_decorator([login_required], name='dispatch')
class MediaDeleteView(DeleteView):
    model = MediaFile

    def get_success_url(self):
        return reverse('media_manager:media_list')

    def get_queryset(self):
        if self.request.user.is_admin():
            return MediaFile.objects.all()
        return MediaFile.objects.filter(uploaded_by=self.request.user)

    def delete(self, request, *args, **kwargs):
        media = self.get_object()
        service = MediaFileService()
        result = service.delete(media.id)
        if result['success']:
            messages.success(request, 'File berhasil dihapus.')
        else:
            messages.error(request, result.get('error', 'Gagal menghapus file.'))
        return redirect(self.get_success_url())


class MediaDownloadView(View):
    def get(self, request, pk):
        service = MediaFileService()
        media = service.get_by_id(pk)
        if not media:
            messages.error(request, 'File tidak ditemukan.')
            return redirect('media_manager:media_list')
        service.increment_download(pk)
        return redirect(media.file.url)

    def post(self, request, pk):
        return self.get(request, pk)
