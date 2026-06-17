from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView, View
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string

from .models import Notification
from .services import NotificationService


@method_decorator(login_required, name='dispatch')
class NotificationListView(ListView):
    model = Notification
    template_name = 'notifications/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        service = NotificationService()
        page = self.request.GET.get('page', 1)
        page_obj, paginator = service.get_paginated(self.request.user, page=int(page))

        notification_type = self.request.GET.get('type')
        if notification_type:
            qs = paginator.object_list.filter(notification_type=notification_type)
        else:
            qs = paginator.object_list

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['types'] = Notification.TYPE_CHOICES
        context['selected_type'] = self.request.GET.get('type', '')
        is_htmx = self.request.headers.get('HX-Request')
        context['is_htmx'] = is_htmx

        if self.request.GET.get('page') and is_htmx:
            context['load_more'] = True
            self.template_name = 'notifications/partials/notification_list_items.html'

        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('HX-Request') and not self.request.GET.get('page'):
            self.template_name = 'notifications/notification_list.html'
        elif self.request.headers.get('HX-Request') and self.request.GET.get('page'):
            self.template_name = 'notifications/partials/notification_list_items.html'
        return super().render_to_response(context, **response_kwargs)


@method_decorator(login_required, name='dispatch')
class MarkReadView(View):
    def post(self, request, pk):
        service = NotificationService()
        result = service.mark_read(pk, request.user)
        if request.headers.get('HX-Request'):
            if result['success']:
                html = render_to_string(
                    'notifications/partials/notification_item.html',
                    {'notification': result['data']},
                    request=request
                )
                return HttpResponse(html, headers={'HX-Trigger': 'notificationCountChanged'})
            return HttpResponse(status=404)
        return JsonResponse(result)


@method_decorator(login_required, name='dispatch')
class MarkAllReadView(View):
    def post(self, request):
        service = NotificationService()
        result = service.mark_all_read(request.user)
        if request.headers.get('HX-Request'):
            return HttpResponse(
                status=200,
                headers={'HX-Trigger': 'notificationCountChanged, notificationListChanged'}
            )
        return JsonResponse(result)


@method_decorator(login_required, name='dispatch')
class GetUnreadView(View):
    def get(self, request):
        service = NotificationService()
        count = service.get_unread_count(request.user)
        unread_notifications = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).order_by('-created_at')[:5]
        if request.headers.get('HX-Request'):
            html = render_to_string(
                'notifications/notification_bell_partial.html',
                {'count': count, 'unread_notifications': unread_notifications},
                request=request
            )
            return HttpResponse(html)
        return JsonResponse({'count': count})
