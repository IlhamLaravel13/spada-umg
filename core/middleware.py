import re
from django.utils import timezone
from django.urls import resolve
from django.contrib import messages


EXEMPT_URLS = [
    r'^/admin/jsi18n/',
    r'^/static/',
    r'^/media/',
    r'^/ckeditor/',
    r'^/api/',
]


class ActivityLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not request.user.is_authenticated:
            return response
        path = request.path_info
        if any(re.match(pattern, path) for pattern in EXEMPT_URLS):
            return response
        self._maybe_log(request, response)
        return response

    def _maybe_log(self, request, response):
        method = request.method
        if method == 'GET' and response.status_code < 400:
            return
        if method == 'POST' and 'login' in request.path:
            return
        log_data = self._build_log_entry(request, method)
        if log_data:
            from .services import ActivityLogService
            ActivityLogService().log(**log_data)

    def _build_log_entry(self, request, method):
        action_map = {
            'POST': 'create',
            'PUT': 'update',
            'PATCH': 'update',
            'DELETE': 'delete',
        }
        action = action_map.get(method, 'view')
        path_parts = request.path.strip('/').split('/')
        model_name = path_parts[0].capitalize() if path_parts else 'Unknown'
        return {
            'user': request.user,
            'action': action,
            'model_name': model_name,
            'object_id': path_parts[-1] if len(path_parts) > 1 and path_parts[-1].isdigit() else '',
            'description': f"{method} {request.path}",
            'ip_address': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')


class NotificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                from notifications.models import Notification
                request.unread_notification_count = Notification.objects.filter(
                    recipient=request.user, is_read=False
                ).count()
            except Exception:
                request.unread_notification_count = 0
        else:
            request.unread_notification_count = 0
        return self.get_response(request)


class ThemeMiddleware:
    COOKIE_NAME = 'theme_preference'
    COOKIE_MAX_AGE = 365 * 24 * 60 * 60

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated:
            theme = request.user.theme_preference
            if request.COOKIES.get(self.COOKIE_NAME) != theme:
                response.set_cookie(
                    self.COOKIE_NAME,
                    theme,
                    max_age=self.COOKIE_MAX_AGE,
                    httponly=False,
                    samesite='Lax',
                )
        return response
