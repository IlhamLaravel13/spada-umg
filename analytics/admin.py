from django.contrib import admin
from django.utils.html import format_html
from .models import AnalyticsCache, UserActivity


@admin.register(AnalyticsCache)
class AnalyticsCacheAdmin(admin.ModelAdmin):
    list_display = ['key', 'created_at', 'expires_at', 'is_expired']
    list_filter = ['created_at', 'expires_at']
    search_fields = ['key']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'

    def is_expired(self, obj):
        from django.utils import timezone
        expired = obj.expires_at <= timezone.now()
        color = 'red' if expired else 'green'
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, 'Expired' if expired else 'Active')
    is_expired.short_description = 'Status'


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'created_at', 'ip_address']
    list_filter = ['action', 'created_at']
    search_fields = ['user__username', 'user__email', 'action', 'ip_address']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']
