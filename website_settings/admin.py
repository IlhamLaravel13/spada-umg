from django.contrib import admin
from .models import SiteSetting


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ['key', 'label', 'group', 'setting_type', 'order', 'is_public', 'updated_at']
    list_filter = ['group', 'setting_type', 'is_public']
    search_fields = ['key', 'label', 'value', 'description']
    list_editable = ['order', 'is_public']
    list_display_links = ['key', 'label']
    fieldsets = [
        ('Setting', {'fields': ['key', 'label', 'group', 'setting_type', 'order']}),
        ('Value', {'fields': ['value', 'is_public', 'description']}),
    ]
