from django.contrib import admin
from django.utils.html import format_html
from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    fields = ['sender', 'body', 'attachment', 'is_read', 'read_at', 'created_at']
    readonly_fields = ['created_at']
    extra = 0
    max_num = 20


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'subject', 'is_group', 'participants_list', 'messages_count', 'updated_at']
    list_filter = ['is_group', 'created_at', 'updated_at']
    search_fields = ['subject', 'participants__username', 'participants__email']
    date_hierarchy = 'updated_at'
    filter_horizontal = ['participants']
    fieldsets = [
        ('Conversation', {'fields': ['participants', 'subject', 'is_group']}),
        ('Timestamps', {'fields': ['created_at', 'updated_at'], 'classes': ['collapse']}),
    ]
    readonly_fields = ['created_at', 'updated_at']
    inlines = [MessageInline]

    def participants_list(self, obj):
        names = [str(u) for u in obj.participants.all()[:3]]
        text = ', '.join(names)
        if obj.participants.count() > 3:
            text += f' +{obj.participants.count() - 3} more'
        return format_html('<span title="{}">{}</span>', text, text)
    participants_list.short_description = 'Participants'

    def messages_count(self, obj):
        count = obj.messages.count()
        return format_html('<span class="badge">{}</span>', count)
    messages_count.short_description = 'Messages'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['short_body', 'conversation', 'sender', 'is_read', 'has_attachment', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['body', 'sender__username', 'conversation__subject']
    list_editable = ['is_read']
    date_hierarchy = 'created_at'
    fieldsets = [
        ('Content', {'fields': ['conversation', 'sender', 'body', 'attachment']}),
        ('Status', {'fields': ['is_read', 'read_at']}),
    ]
    readonly_fields = ['created_at', 'read_at']

    def short_body(self, obj):
        return obj.body[:75] + '...' if len(obj.body) > 75 else obj.body
    short_body.short_description = 'Body'

    def has_attachment(self, obj):
        if obj.attachment:
            return format_html('<i class="fas fa-paperclip" style="color: green;"></i>')
        return format_html('<i class="fas fa-times" style="color: #ccc;"></i>')
    has_attachment.short_description = 'Attachment'
