from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.urls import reverse_lazy, reverse
from django.http import HttpResponse, Http404, FileResponse
from django.db.models import Count, Q
import mimetypes
import os

from .models import LibraryItem, LibraryCategory
from .services import LibraryService


@method_decorator(login_required, name='dispatch')
class LibraryListView(ListView):
    template_name = 'library/library_list.html'
    context_object_name = 'items'
    paginate_by = 12

    def get_queryset(self):
        service = LibraryService()
        return service.get_catalog(self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = LibraryService()
        context['categories'] = service.get_categories_with_count()
        context['type_summary'] = service.get_type_summary()
        context['current_type'] = self.request.GET.get('type')
        context['current_category'] = self.request.GET.get('category')
        context['current_faculty'] = self.request.GET.get('faculty')
        context['current_year'] = self.request.GET.get('year')
        context['current_q'] = self.request.GET.get('q', '')
        context['years'] = LibraryItem.objects.filter(is_published=True).values_list(
            'publication_year', flat=True
        ).distinct().order_by('-publication_year')
        return context


@method_decorator(login_required, name='dispatch')
class LibraryDetailView(DetailView):
    model = LibraryItem
    template_name = 'library/library_detail.html'
    context_object_name = 'item'

    def get_object(self, queryset=None):
        obj = get_object_or_404(
            LibraryItem.objects.select_related(
                'category', 'faculty', 'study_program', 'uploaded_by'
            ),
            pk=self.kwargs['pk'], is_published=True
        )
        LibraryService().increment_view(obj.id)
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = context['item']
        context['related_items'] = LibraryItem.objects.filter(
            is_published=True
        ).filter(
            Q(category=item.category) | Q(item_type=item.item_type)
        ).exclude(id=item.id)[:5]
        return context


@method_decorator(login_required, name='dispatch')
class LibraryDownloadView(View):
    def get(self, request, pk):
        item = get_object_or_404(LibraryItem, pk=pk, is_published=True)
        if not item.file:
            messages.error(request, 'File tidak tersedia')
            return redirect('library:detail', pk=pk)

        LibraryService().increment_download(pk)

        file_path = item.file.path
        if not os.path.exists(file_path):
            messages.error(request, 'File tidak ditemukan di server')
            return redirect('library:detail', pk=pk)

        filename = f"{item.title}.{item.file.name.split('.')[-1]}"
        response = FileResponse(
            open(file_path, 'rb'),
            as_attachment=True,
            filename=filename
        )
        return response


@method_decorator(login_required, name='dispatch')
class LibraryCreateView(CreateView):
    model = LibraryItem
    template_name = 'library/library_form.html'
    fields = [
        'title', 'author', 'description', 'item_type', 'category',
        'faculty', 'study_program', 'file', 'cover_image', 'publisher',
        'publication_year', 'isbn', 'pages', 'language', 'tags',
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = False
        context['categories'] = LibraryCategory.objects.filter(is_active=True)
        return context

    def form_valid(self, form):
        service = LibraryService()
        data = {k: form.cleaned_data[k] for k in form.cleaned_data}
        data['uploaded_by'] = self.request.user
        result = service.upload_item(self.request.user.id, **data)
        if result['success']:
            messages.success(self.request, 'Item perpustakaan berhasil ditambahkan')
            return redirect('library:detail', pk=result['item'].id)
        messages.error(self.request, result['error'])
        return self.form_invalid(form)

    def get_success_url(self):
        return reverse('library:list')


@method_decorator(login_required, name='dispatch')
class LibraryUpdateView(UpdateView):
    model = LibraryItem
    template_name = 'library/library_form.html'
    fields = [
        'title', 'author', 'description', 'item_type', 'category',
        'faculty', 'study_program', 'file', 'cover_image', 'publisher',
        'publication_year', 'isbn', 'pages', 'language', 'tags',
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        context['categories'] = LibraryCategory.objects.filter(is_active=True)
        return context

    def form_valid(self, form):
        service = LibraryService()
        data = {k: form.cleaned_data[k] for k in form.cleaned_data if form.cleaned_data[k] is not None}
        result = service.update_item(self.get_object().id, self.request.user, **data)
        if result['success']:
            messages.success(self.request, 'Item perpustakaan berhasil diperbarui')
            return redirect('library:detail', pk=self.get_object().id)
        messages.error(self.request, result['error'])
        return self.form_invalid(form)

    def get_success_url(self):
        return reverse('library:detail', kwargs={'pk': self.object.id})


@method_decorator(login_required, name='dispatch')
class LibraryDeleteView(DeleteView):
    model = LibraryItem

    def post(self, request, *args, **kwargs):
        item = self.get_object()
        service = LibraryService()
        result = service.delete_item(item.id, request.user)
        if result['success']:
            messages.success(request, 'Item berhasil dihapus')
        else:
            messages.error(request, result['error'])
        return redirect('library:list')

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('library:list')


@method_decorator(login_required, name='dispatch')
class LibraryCategoryListView(ListView):
    template_name = 'library/library_category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return LibraryCategory.objects.filter(is_active=True).annotate(
            item_count=Count('libraryitem', filter=Q(libraryitem__is_published=True))
        ).order_by('name')
