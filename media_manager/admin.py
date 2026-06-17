from django.contrib import admin
from django.utils.html import format_html
from .models import MediaFile


@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = ['title', 'file_type', 'file_size_display', 'is_public', 'uploaded_by', 'download_count', 'created_at', 'preview_link']
    list_filter = ['file_type', 'is_public', 'created_at']
    search_fields = ['title', 'description', 'tags', 'alt_text']
    list_editable = ['is_public']
    date_hierarchy = 'created_at'
    readonly_fields = ['file_size', 'mime_type', 'download_count', 'created_at', 'updated_at', 'preview_link']
    fieldsets = [
        ('Content', {'fields': ['title', 'description', 'file', 'thumbnail', 'alt_text', 'tags']}),
        ('Type & Size', {'fields': ['file_type', 'mime_type', 'file_size']}),
        ('Status', {'fields': ['is_public', 'uploaded_by', 'download_count']}),
        ('Timestamps', {'fields': ['created_at', 'updated_at']}),
    ]

    def file_size_display(self, obj):
        if obj.file_size < 1024:
            return f"{obj.file_size} B"
        elif obj.file_size < 1024 * 1024:
            return f"{obj.file_size / 1024:.1f} KB"
        return f"{obj.file_size / (1024 * 1024):.1f} MB"
    file_size_display.short_description = 'Size'

    def preview_link(self, obj):
        if obj.pk:
            return format_html('<a href="{}" target="_blank" class="button">View File</a>', obj.file.url)
        return '-'
    preview_link.short_description = 'Preview'
