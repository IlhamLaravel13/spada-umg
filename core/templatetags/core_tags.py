from django import template
from django.utils import timezone
from django.template.defaultfilters import date as date_filter
from django.urls import resolve
import math

register = template.Library()


@register.simple_tag(takes_context=True)
def has_perm(context, perm):
    request = context.get('request')
    if request and request.user.is_authenticated:
        return request.user.has_perm(perm)
    return False


@register.simple_tag(takes_context=True)
def user_role(context):
    request = context.get('request')
    if request and request.user.is_authenticated:
        return request.user.role
    return ''


@register.simple_tag(takes_context=True)
def active_class(context, url_name, css_class='active'):
    request = context.get('request')
    if not request:
        return ''
    try:
        current_url_name = resolve(request.path).url_name
        if current_url_name == url_name:
            return css_class
    except Exception:
        pass
    return ''


@register.filter
def format_date(value, fmt='d F Y'):
    if not value:
        return ''
    return date_filter(value, fmt)


@register.filter
def time_ago(value):
    if not value:
        return ''
    now = timezone.now()
    if isinstance(value, str):
        from django.utils.dateparse import parse_datetime
        value = parse_datetime(value)
    diff = now - value
    if value > now:
        return 'baru saja'
    seconds = diff.total_seconds()
    if seconds < 60:
        return 'baru saja'
    minutes = int(seconds // 60)
    if minutes < 60:
        return f'{minutes} menit yang lalu'
    hours = int(minutes // 60)
    if hours < 24:
        return f'{hours} jam yang lalu'
    days = int(hours // 24)
    if days < 7:
        return f'{days} hari yang lalu'
    weeks = int(days // 7)
    if weeks < 4:
        return f'{weeks} minggu yang lalu'
    months = int(days // 30)
    if months < 12:
        return f'{months} bulan yang lalu'
    years = int(days // 365)
    return f'{years} tahun yang lalu'


@register.filter
def file_size(value):
    if not value:
        return '0 B'
    if isinstance(value, str):
        try:
            value = float(value)
        except (ValueError, TypeError):
            return value
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = float(value)
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    if unit_index == 0:
        return f'{int(size)} {units[unit_index]}'
    return f'{size:.1f} {units[unit_index]}'


@register.filter
def file_icon(value):
    if not value:
        return 'fa-regular fa-file'
    ext = value.lower().split('.')[-1] if '.' in value else ''
    icon_map = {
        'pdf': 'fa-regular fa-file-pdf',
        'doc': 'fa-regular fa-file-word',
        'docx': 'fa-regular fa-file-word',
        'xls': 'fa-regular fa-file-excel',
        'xlsx': 'fa-regular fa-file-excel',
        'ppt': 'fa-regular fa-file-powerpoint',
        'pptx': 'fa-regular fa-file-powerpoint',
        'jpg': 'fa-regular fa-file-image',
        'jpeg': 'fa-regular fa-file-image',
        'png': 'fa-regular fa-file-image',
        'gif': 'fa-regular fa-file-image',
        'svg': 'fa-regular fa-file-image',
        'webp': 'fa-regular fa-file-image',
        'mp4': 'fa-regular fa-file-video',
        'avi': 'fa-regular fa-file-video',
        'mov': 'fa-regular fa-file-video',
        'mp3': 'fa-regular fa-file-audio',
        'wav': 'fa-regular fa-file-audio',
        'zip': 'fa-regular fa-file-zipper',
        'rar': 'fa-regular fa-file-zipper',
        '7z': 'fa-regular fa-file-zipper',
        'tar': 'fa-regular fa-file-zipper',
        'gz': 'fa-regular fa-file-zipper',
        'txt': 'fa-regular fa-file-lines',
        'py': 'fa-regular fa-file-code',
        'js': 'fa-regular fa-file-code',
        'html': 'fa-regular fa-file-code',
        'css': 'fa-regular fa-file-code',
        'json': 'fa-regular fa-file-code',
        'xml': 'fa-regular fa-file-code',
    }
    return icon_map.get(ext, 'fa-regular fa-file')


@register.filter
def lookup(d, key):
    if not isinstance(d, dict):
        try:
            return getattr(d, str(key), None)
        except Exception:
            return None
    return d.get(key, 0)


@register.inclusion_tag('core/notification_bell.html', takes_context=True)
def notification_bell(context):
    request = context.get('request')
    count = getattr(request, 'unread_notification_count', 0) if request else 0
    return {'count': count, 'user': request.user if request else None}
