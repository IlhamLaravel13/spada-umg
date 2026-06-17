from django.contrib import admin
from django.utils.html import format_html
from .models import LibraryCategory, LibraryItem


@admin.register(LibraryCategory)
class LibraryCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon_display', 'is_active', 'item_count', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at']

    def icon_display(self, obj):
        return format_html('<i class="fas fa-{}"></i>', obj.icon)
    icon_display.short_description = 'Icon'

    def item_count(self, obj):
        return obj.libraryitem_set.count()
    item_count.short_description = 'Items'


@admin.register(LibraryItem)
class LibraryItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'item_type', 'category', 'faculty', 'download_count', 'view_count', 'is_published', 'created_at']
    list_filter = ['item_type', 'is_published', 'category', 'faculty', 'language']
    search_fields = ['title', 'author', 'description', 'publisher', 'isbn', 'tags']
    list_editable = ['is_published']
    date_hierarchy = 'created_at'
    readonly_fields = ['download_count', 'view_count', 'created_at', 'updated_at']
    fieldsets = (
        (None, {
            'fields': ('title', 'author', 'description', 'item_type', 'category')
        }),
        ('Institusi', {
            'fields': ('faculty', 'study_program')
        }),
        ('File & Cover', {
            'fields': ('file', 'cover_image')
        }),
        ('Detail Publikasi', {
            'fields': ('publisher', 'publication_year', 'isbn', 'pages', 'language')
        }),
        ('Lainnya', {
            'fields': ('tags', 'uploaded_by', 'is_published')
        }),
        ('Statistik', {
            'fields': ('download_count', 'view_count'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category', 'faculty', 'study_program', 'uploaded_by')
