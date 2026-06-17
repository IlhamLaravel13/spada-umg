from django.contrib import admin
from django.utils.html import format_html
from .models import AttendanceSession, Attendance

@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ['title', 'class_meta', 'date', 'start_time', 'end_time', 'meeting_number', 'is_active', 'show_qr']
    list_filter = ['is_active', 'date', 'class_meta__course']
    search_fields = ['title', 'topic', 'class_meta__course__name', 'class_meta__code']
    list_editable = ['is_active']
    date_hierarchy = 'date'
    fieldsets = [
        ('Session Info', {'fields': ['class_meta', 'title', 'topic', 'meeting_number']}),
        ('Schedule', {'fields': ['date', 'start_time', 'end_time']}),
        ('QR Code', {'fields': ['qr_code', 'qr_code_secret']}),
        ('Status', {'fields': ['is_active', 'created_by']}),
    ]
    readonly_fields = ['created_at']

    def show_qr(self, obj):
        if obj.qr_code:
            return format_html('<img src="{}" width="50" height="50" style="border-radius:8px" />', obj.qr_code.url)
        return '-'
    show_qr.short_description = 'QR'

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'session', 'status', 'check_in_time', 'verified_by']
    list_filter = ['status', 'session__date', 'session__class_meta']
    search_fields = ['student__username', 'student__nim', 'student__email', 'notes']
    list_editable = ['status']
    date_hierarchy = 'check_in_time'
    fieldsets = [
        ('Attendance Data', {'fields': ['session', 'student', 'status']}),
        ('Check-in Info', {'fields': ['check_in_time', 'latitude', 'longitude']}),
        ('Notes', {'fields': ['notes', 'verified_by']}),
    ]
    readonly_fields = ['check_in_time']
