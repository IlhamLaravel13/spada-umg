from django.shortcuts import render
from django.views.generic import TemplateView, View
from django.http import JsonResponse, HttpResponseNotFound, HttpResponseServerError
from django.db.models import Count, Q
from django.utils import timezone
from django.conf import settings
from django.template.loader import render_to_string

from .services import SearchService


class LandingPageView(TemplateView):
    template_name = 'core/landing.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = self._get_stats()
        context['announcements'] = self._get_announcements()
        context['news'] = self._get_news()
        context['calendar_events'] = self._get_calendar_events()
        context['campus_background'] = self._get_campus_background()
        return context

    def _get_stats(self):
        stats = {'mahasiswa': 0, 'dosen': 0, 'mata_kuliah': 0, 'kelas': 0}
        try:
            from accounts.models import User
            stats['mahasiswa'] = User.objects.filter(role='mahasiswa', is_active=True).count()
            stats['dosen'] = User.objects.filter(role='dosen', is_active=True).count()
        except Exception:
            pass
        try:
            from academics.models import Course
            stats['mata_kuliah'] = Course.objects.filter(is_active=True).count()
        except Exception:
            pass
        try:
            stats['kelas'] = stats['mata_kuliah']
        except Exception:
            pass
        return stats

    def _get_announcements(self):
        try:
            from announcements.models import Announcement
            return Announcement.objects.filter(
                is_published=True
            ).order_by('-created_at')[:5]
        except Exception:
            return []

    def _get_news(self):
        try:
            from announcements.models import Announcement
            return Announcement.objects.filter(
                is_published=True, is_news=True
            ).order_by('-created_at')[:3]
        except Exception:
            return []

    def _get_calendar_events(self):
        try:
            from academics.models import AcademicEvent
            return AcademicEvent.objects.filter(
                event_date__gte=timezone.now().date()
            ).order_by('event_date')[:6]
        except Exception:
            return []

    def _get_campus_background(self):
        try:
            from .models import CampusBackground
            bg = CampusBackground.objects.filter(page='landing', is_active=True).first()
            if bg and bg.image:
                return bg.image.url
        except Exception:
            pass
        return ''


class BackgroundImageView(View):
    def get(self, request, page):
        try:
            from .models import CampusBackground
            bg = CampusBackground.objects.filter(page=page, is_active=True).first()
            if bg and bg.image:
                return JsonResponse({
                    'image_url': bg.image.url,
                    'overlay_opacity': bg.overlay_opacity,
                })
        except Exception:
            pass
        return JsonResponse({'image_url': '', 'overlay_opacity': 0.35})


class SearchView(TemplateView):
    template_name = 'core/search.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '').strip()
        context['query'] = query
        if query and len(query) >= 2:
            service = SearchService()
            search_results = service.search_all(query, self.request.user)
            context['search_results'] = search_results.get('results', {})
            context['total_results'] = search_results.get('total', 0)
        else:
            context['search_results'] = {}
            context['total_results'] = 0
        return context


class VercelHandlerView(View):
    def get(self, request, *args, **kwargs):
        return JsonResponse({'status': 'ok', 'message': 'SPADA UMG API'})


def handler404(request, exception=None):
    return HttpResponseNotFound(render_to_string('core/404.html', {}, request))


def handler500(request):
    return HttpResponseServerError(render_to_string('core/500.html', {}, request))
