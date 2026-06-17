from django.contrib import admin
from django.utils.html import format_html
from .models import Announcement, AnnouncementRead


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'audience', 'is_important', 'is_published', 'created_by', 'created_at', 'reads_count']
    list_filter = ['category', 'audience', 'is_important', 'is_published', 'created_at']
    search_fields = ['title', 'content']
    list_editable = ['is_important', 'is_published']
    date_hierarchy = 'created_at'
    fieldsets = [
        ('Content', {'fields': ['title', 'content', 'category']}),
        ('Targeting', {'fields': ['audience', 'target_class']}),
        ('Status', {'fields': ['is_important', 'is_published', 'pinned_until']}),
        ('Attachment', {'fields': ['attachment']}),
        ('Meta', {'fields': ['created_by']}),
    ]
    readonly_fields = ['created_at', 'updated_at']

    def reads_count(self, obj):
        count = obj.reads.count()
        return format_html('<span class="badge">{}</span>', count)
    reads_count.short_description = 'Reads'


@admin.register(AnnouncementRead)
class AnnouncementReadAdmin(admin.ModelAdmin):
    list_display = ['announcement', 'user', 'read_at']
    list_filter = ['read_at']
    search_fields = ['announcement__title', 'user__username', 'user__email']
    date_hierarchy = 'read_at'
    readonly_fields = ['read_at']
