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

from .models import Announcement
from .services import AnnouncementService


def is_admin_or_dosen(user):
    return user.is_authenticated and (user.is_dosen() or user.is_admin())


class HTMXMixin:
    def htmx_render(self, template, context):
        if self.request.headers.get('HX-Request'):
            return render(self.request, template, context)
        return render(self.request, template, context)


class AnnouncementListView(HTMXMixin, ListView):
    model = Announcement
    template_name = 'announcements/announcement_list.html'
    context_object_name = 'announcements'
    paginate_by = 20

    def get_queryset(self):
        service = AnnouncementService()
        if self.request.user.is_authenticated and (self.request.user.is_dosen() or self.request.user.is_admin()):
            qs = service.get_all()
        else:
            qs = service.get_for_user(self.request.user)
            if self.request.user.is_authenticated:
                qs = qs | service.get_all().filter(audience='all', is_published=True)
            else:
                qs = service.get_published().filter(audience='all')

        if self.request.user.is_authenticated:
            unread_ids = set()
            for a in qs:
                if not a.reads.filter(user=self.request.user).exists():
                    unread_ids.add(a.id)
            self.unread_ids = unread_ids

        query = self.request.GET.get('q')
        if query:
            qs = qs.filter(Q(title__icontains=query) | Q(content__icontains=query))
        category = self.request.GET.get('category')
        if category:
            qs = qs.filter(category=category)
        return qs.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Announcement.CATEGORY_CHOICES
        context['selected_category'] = self.request.GET.get('category')
        if hasattr(self, 'unread_ids'):
            context['unread_ids'] = self.unread_ids
        else:
            context['unread_ids'] = set()
        service = AnnouncementService()
        if self.request.user.is_authenticated:
            context['unread_count'] = service.get_unread_count(self.request.user)
            context['important_announcements'] = service.get_important()
        return context


class AnnouncementDetailView(DetailView):
    model = Announcement
    template_name = 'announcements/announcement_detail.html'
    context_object_name = 'announcement'

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if request.user.is_authenticated:
            service = AnnouncementService()
            service.mark_as_read(request.user, self.object.id)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['other_announcements'] = Announcement.objects.filter(
            is_published=True,
            category=self.object.category,
        ).exclude(id=self.object.id)[:5]
        return context


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class AnnouncementCreateView(CreateView):
    model = Announcement
    template_name = 'announcements/announcement_form.html'
    fields = [
        'title', 'content', 'category', 'audience', 'target_class',
        'is_important', 'is_published', 'attachment', 'pinned_until',
    ]
    success_url = reverse_lazy('announcements:announcement_list')

    def form_valid(self, form):
        service = AnnouncementService()
        result = service.create(
            title=form.cleaned_data['title'],
            content=form.cleaned_data['content'],
            category=form.cleaned_data.get('category', 'umum'),
            audience=form.cleaned_data.get('audience', 'all'),
            target_class=form.cleaned_data.get('target_class'),
            is_important=form.cleaned_data.get('is_important', False),
            is_published=form.cleaned_data.get('is_published', True),
            attachment=form.cleaned_data.get('attachment'),
            pinned_until=form.cleaned_data.get('pinned_until'),
            created_by=self.request.user,
        )
        if result['success']:
            messages.success(self.request, 'Pengumuman berhasil dibuat.')
            if self.request.headers.get('HX-Request'):
                return HttpResponse(status=201, headers={'HX-Trigger': 'announcementListChanged'})
            return redirect(self.success_url)
        messages.error(self.request, result['error'])
        return self.form_invalid(form)

    def form_invalid(self, form):
        if self.request.headers.get('HX-Request'):
            html = render_to_string(self.template_name, {'form': form}, request=self.request)
            return HttpResponse(html, status=422)
        return super().form_invalid(form)


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class AnnouncementUpdateView(UpdateView):
    model = Announcement
    template_name = 'announcements/announcement_form.html'
    fields = [
        'title', 'content', 'category', 'audience', 'target_class',
        'is_important', 'is_published', 'attachment', 'pinned_until',
    ]
    success_url = reverse_lazy('announcements:announcement_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        return context

    def form_valid(self, form):
        service = AnnouncementService()
        result = service.update(self.get_object().id, **form.cleaned_data)
        if result['success']:
            messages.success(self.request, 'Pengumuman berhasil diperbarui.')
            if self.request.headers.get('HX-Request'):
                return HttpResponse(status=200, headers={'HX-Trigger': 'announcementListChanged'})
            return redirect(self.success_url)
        messages.error(self.request, result['error'])
        return self.form_invalid(form)


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class AnnouncementDeleteView(DeleteView):
    model = Announcement
    success_url = reverse_lazy('announcements:announcement_list')

    def delete(self, request, *args, **kwargs):
        service = AnnouncementService()
        result = service.delete(kwargs.get('pk'))
        if result['success']:
            messages.success(request, result['message'])
        else:
            messages.error(request, result['error'])
        if request.headers.get('HX-Request'):
            return HttpResponse(status=200, headers={'HX-Trigger': 'announcementListChanged'})
        return redirect(self.success_url)


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class AnnouncementTogglePublishView(View):
    def post(self, request, *args, **kwargs):
        service = AnnouncementService()
        announcement = service.get_by_id(kwargs.get('pk'))
        if not announcement:
            messages.error(request, 'Announcement not found')
            return redirect('announcements:announcement_list')
        result = service.toggle_publish(announcement.id)
        if result['success']:
            messages.success(request, f'Announcement {"published" if not announcement.is_published else "unpublished"}')
        else:
            messages.error(request, result['error'])
        return redirect(request.META.get('HTTP_REFERER', 'announcements:announcement_list'))


@method_decorator([login_required, user_passes_test(is_admin_or_dosen)], name='dispatch')
class AnnouncementToggleImportantView(View):
    def post(self, request, *args, **kwargs):
        service = AnnouncementService()
        announcement = service.get_by_id(kwargs.get('pk'))
        if not announcement:
            messages.error(request, 'Announcement not found')
            return redirect('announcements:announcement_list')
        result = service.toggle_important(announcement.id)
        if result['success']:
            messages.success(request, 'Importance toggled')
        else:
            messages.error(request, result['error'])
        return redirect(request.META.get('HTTP_REFERER', 'announcements:announcement_list'))


@login_required
def mark_as_read(request, pk):
    service = AnnouncementService()
    result = service.mark_as_read(request.user, pk)
    if request.headers.get('HX-Request'):
        if result['success']:
            return HttpResponse(status=200, headers={'HX-Trigger': 'announcementReadChanged'})
        return HttpResponse(status=404)
    return JsonResponse(result)


@login_required
def mark_all_as_read(request):
    service = AnnouncementService()
    result = service.mark_all_as_read(request.user)
    if request.headers.get('HX-Request'):
        return HttpResponse(status=200, headers={'HX-Trigger': 'announcementReadChanged'})
    return JsonResponse(result)


def announcement_banner(request):
    service = AnnouncementService()
    if request.user.is_authenticated:
        important = service.get_important().exclude(reads__user=request.user)
    else:
        important = service.get_important().filter(audience='all')
    return render(request, 'announcements/announcement_banner.html', {'important_announcements': important})
