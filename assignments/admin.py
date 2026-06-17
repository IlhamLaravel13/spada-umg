from django.contrib import admin
from .models import Assignment, AssignmentSubmission, AssignmentSubmissionAttachment


class AssignmentSubmissionInline(admin.TabularInline):
    model = AssignmentSubmission
    extra = 0
    readonly_fields = ['submitted_at', 'graded_at']


class AssignmentSubmissionAttachmentInline(admin.TabularInline):
    model = AssignmentSubmissionAttachment
    extra = 0
    readonly_fields = ['uploaded_at']


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'class_meta', 'max_score', 'due_date', 'is_published', 'is_group_assignment', 'created_at']
    list_filter = ['is_published', 'is_group_assignment', 'allow_late_submission', 'class_meta__course']
    search_fields = ['title', 'description', 'instructions']
    list_editable = ['is_published']
    date_hierarchy = 'due_date'
    fieldsets = [
        ('Basic Information', {'fields': ['class_meta', 'title', 'description', 'instructions']}),
        ('Grading', {'fields': ['max_score', 'passing_score']}),
        ('Timeline', {'fields': ['due_date', 'allow_late_submission', 'late_penalty_percent']}),
        ('Submission Rules', {'fields': ['max_attempts', 'is_group_assignment', 'file_required', 'allowed_file_types']}),
        ('Status', {'fields': ['is_published', 'created_by']}),
    ]
    inlines = [AssignmentSubmissionInline]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ['student', 'assignment', 'status', 'score', 'attempt_number', 'submitted_at', 'graded_at']
    list_filter = ['status', 'assignment']
    search_fields = ['student__username', 'student__nim', 'student__email', 'assignment__title']
    list_editable = ['score', 'status']
    readonly_fields = ['submitted_at', 'graded_at']
    fieldsets = [
        ('Submission', {'fields': ['assignment', 'student', 'file', 'notes']}),
        ('Grading', {'fields': ['score', 'feedback', 'status', 'graded_by', 'graded_at']}),
        ('Metadata', {'fields': ['attempt_number', 'submitted_at']}),
    ]
    inlines = [AssignmentSubmissionAttachmentInline]


@admin.register(AssignmentSubmissionAttachment)
class AssignmentSubmissionAttachmentAdmin(admin.ModelAdmin):
    list_display = ['original_name', 'submission', 'file_size', 'uploaded_at']
    search_fields = ['original_name']
    readonly_fields = ['uploaded_at']
