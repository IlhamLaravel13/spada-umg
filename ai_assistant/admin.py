from django.contrib import admin
from django.utils.html import format_html
from .models import AIProvider, AIConversation, AIMessage


@admin.register(AIProvider)
class AIProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'model', 'is_active', 'key_preview', 'created_at']
    list_filter = ['is_active', 'name']
    search_fields = ['name', 'model']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        (None, {
            'fields': ('name', 'api_key', 'model', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def key_preview(self, obj):
        if obj.api_key:
            return format_html('<code>{}...{}</code>', obj.api_key[:8], obj.api_key[-4:])
        return '-'
    key_preview.short_description = 'API Key'


class AIMessageInline(admin.TabularInline):
    model = AIMessage
    extra = 0
    readonly_fields = ['role', 'content', 'metadata', 'created_at']
    fields = ['role', 'content', 'created_at']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'message_count', 'created_at', 'updated_at']
    list_filter = ['created_at']
    search_fields = ['title', 'user__username', 'user__email']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']
    inlines = [AIMessageInline]

    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'


@admin.register(AIMessage)
class AIMessageAdmin(admin.ModelAdmin):
    list_display = ['short_content', 'conversation', 'role', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['content', 'conversation__title']
    readonly_fields = ['conversation', 'role', 'content', 'metadata', 'created_at']

    def short_content(self, obj):
        return obj.content[:75] + '...' if len(obj.content) > 75 else obj.content
    short_content.short_description = 'Content'

    def has_add_permission(self, request):
        return False
