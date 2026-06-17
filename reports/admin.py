from django.contrib import admin
from .models import Report

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'report_type', 'format', 'generated_by', 'is_ready', 'created_at']
    list_filter = ['report_type', 'format', 'is_ready', 'created_at']
    search_fields = ['title', 'generated_by__username', 'generated_by__email']
    list_editable = ['is_ready']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']
    fieldsets = (
        (None, {'fields': ('title', 'report_type', 'format')}),
        ('Parameters', {'fields': ('parameters',)}),
        ('File', {'fields': ('file', 'is_ready')}),
        ('Audit', {'fields': ('generated_by', 'created_at')}),
    )
