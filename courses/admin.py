from django.contrib import admin
from .models import Material, MaterialComment, CourseProgress


class MaterialCommentInline(admin.TabularInline):
    model = MaterialComment
    extra = 0
    readonly_fields = ['user', 'comment', 'created_at']


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'class_meta', 'file_type', 'file_size', 'order',
        'is_published', 'allow_download', 'uploaded_by', 'created_at'
    ]
    list_filter = ['file_type', 'is_published', 'class_meta']
    search_fields = ['title', 'description', 'class_meta__name', 'class_meta__course__name']
    list_editable = ['order', 'is_published', 'allow_download']
    list_per_page = 25
    date_hierarchy = 'created_at'
    inlines = [MaterialCommentInline]
    fieldsets = (
        (None, {
            'fields': ('class_meta', 'title', 'description', 'uploaded_by')
        }),
        ('File', {
            'fields': ('file_type', 'file', 'file_url', 'file_size')
        }),
        ('Settings', {
            'fields': ('is_published', 'allow_download', 'order')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'class_meta', 'class_meta__course', 'uploaded_by'
        )


@admin.register(MaterialComment)
class MaterialCommentAdmin(admin.ModelAdmin):
    list_display = ['material', 'user', 'comment_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['comment', 'user__username', 'material__title']
    readonly_fields = ['material', 'user', 'comment', 'created_at']

    def comment_preview(self, obj):
        return obj.comment[:75] + '...' if len(obj.comment) > 75 else obj.comment
    comment_preview.short_description = 'Comment'

    def has_add_permission(self, request):
        return False


@admin.register(CourseProgress)
class CourseProgressAdmin(admin.ModelAdmin):
    list_display = ['student', 'class_meta', 'material', 'is_completed', 'completed_at']
    list_filter = ['is_completed', 'class_meta']
    search_fields = ['student__username', 'student__nim', 'material__title']
    list_editable = ['is_completed']
    date_hierarchy = 'completed_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'student', 'class_meta', 'material'
        )
