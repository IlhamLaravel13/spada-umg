from django.contrib import admin
from .models import ActivityLog, SystemConfig, CampusBackground


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'model_name', 'object_id', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['user__username', 'user__email', 'model_name', 'description']
    readonly_fields = ['user', 'action', 'model_name', 'object_id', 'description', 'ip_address', 'user_agent', 'created_at']
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'is_public', 'updated_at']
    list_filter = ['is_public']
    search_fields = ['key', 'value', 'description']
    list_editable = ['value', 'is_public']
    ordering = ['key']


@admin.register(CampusBackground)
class CampusBackgroundAdmin(admin.ModelAdmin):
    list_display = ['page', 'is_active', 'overlay_opacity', 'updated_at']
    list_filter = ['page', 'is_active']
    list_editable = ['is_active', 'overlay_opacity']
