from django.contrib import admin
from django.utils.html import format_html
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'recipient', 'notification_type_colored', 'is_read', 'is_important', 'sent_email', 'created_at']
    list_filter = ['notification_type', 'is_read', 'is_important', 'sent_email', 'created_at']
    search_fields = ['title', 'message', 'recipient__username', 'recipient__email']
    list_editable = ['is_read', 'is_important']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'read_at']
    fieldsets = [
        ('Recipient', {'fields': ['recipient']}),
        ('Content', {'fields': ['notification_type', 'title', 'message', 'link']}),
        ('Status', {'fields': ['is_read', 'read_at', 'is_important', 'sent_email']}),
        ('Meta', {'fields': ['created_at']}),
    ]

    def notification_type_colored(self, obj):
        colors = {
            'info': 'blue', 'success': 'green', 'warning': 'yellow',
            'danger': 'red', 'assignment': 'indigo', 'quiz': 'purple',
            'grade': 'teal', 'announcement': 'orange', 'forum': 'cyan',
            'message': 'sky', 'payment': 'emerald', 'certificate': 'amber',
        }
        color = colors.get(obj.notification_type, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_notification_type_display()
        )
    notification_type_colored.short_description = 'Type'
