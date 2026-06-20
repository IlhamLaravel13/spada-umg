from django.conf import settings
from django.db.utils import OperationalError
from .services import SystemConfigService


def _default_site_settings():
    return {
        'site_name': 'SPADA UMG',
        'site_tagline': 'Sistem Pembelajaran Daring',
        'site_logo': '',
        'site_description': 'Platform pembelajaran daring Universitas Muhammadiyah Gresik',
        'contact_email': 'info@umg.ac.id',
        'contact_phone': '(031) 1234567',
        'contact_address': 'Jl. Sumatera No. 101, Gresik 61121',
        'footer_text': 'Universitas Muhammadiyah Gresik',
        'social_facebook': '#',
        'social_twitter': '#',
        'social_instagram': '#',
        'social_youtube': '#',
        'social_linkedin': '#',
    }


def site_settings(request):
    try:
        config_service = SystemConfigService()
        return {
            'site_name': config_service.get('site_name', 'SPADA UMG'),
            'site_tagline': config_service.get('site_tagline', 'Sistem Pembelajaran Daring'),
            'site_logo': config_service.get('site_logo', ''),
            'site_description': config_service.get('site_description', 'Platform pembelajaran daring Universitas Muhammadiyah Gresik'),
            'contact_email': config_service.get('contact_email', 'info@umg.ac.id'),
            'contact_phone': config_service.get('contact_phone', '(031) 1234567'),
            'contact_address': config_service.get('contact_address', 'Jl. Sumatera No. 101, Gresik 61121'),
            'footer_text': config_service.get('footer_text', 'Universitas Muhammadiyah Gresik'),
            'social_facebook': config_service.get('social_facebook', '#'),
            'social_twitter': config_service.get('social_twitter', '#'),
            'social_instagram': config_service.get('social_instagram', '#'),
            'social_youtube': config_service.get('social_youtube', '#'),
            'social_linkedin': config_service.get('social_linkedin', '#'),
        }
    except OperationalError:
        return _default_site_settings()


def notification_count(request):
    if request.user.is_authenticated:
        count = getattr(request, 'unread_notification_count', 0)
    else:
        count = 0
    return {'unread_notification_count': count}


def theme_preference(request):
    if request.user.is_authenticated:
        theme = request.user.theme_preference
    else:
        theme = request.COOKIES.get('theme_preference', 'light')
    return {'user_theme_preference': theme, 'is_dark_mode': theme == 'dark'}
