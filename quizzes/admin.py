from django.contrib import admin
from .models import Quiz, QuizQuestion, QuizAnswer, QuizAttempt, QuizResponse


class QuizAnswerInline(admin.TabularInline):
    model = QuizAnswer
    extra = 2
    fields = ['answer_text', 'is_correct']


class QuizQuestionInline(admin.TabularInline):
    model = QuizQuestion
    extra = 1
    fields = ['question_text', 'question_type', 'points', 'order']
    show_change_link = True


class QuizResponseInline(admin.TabularInline):
    model = QuizResponse
    extra = 0
    readonly_fields = ['question', 'selected_answer', 'essay_answer', 'is_correct', 'points_earned']
    can_delete = False


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'class_meta', 'time_limit_minutes', 'max_attempts', 'passing_score', 'is_published', 'due_date', 'created_at']
    list_filter = ['is_published', 'shuffle_questions', 'show_result_immediately']
    search_fields = ['title', 'description']
    list_editable = ['is_published']
    date_hierarchy = 'due_date'
    fieldsets = [
        ('Basic Information', {'fields': ['class_meta', 'title', 'description']}),
        ('Settings', {'fields': ['time_limit_minutes', 'max_attempts', 'passing_score']}),
        ('Options', {'fields': ['shuffle_questions', 'show_result_immediately']}),
        ('Timeline', {'fields': ['due_date', 'is_published']}),
        ('Creator', {'fields': ['created_by']}),
    ]
    inlines = [QuizQuestionInline]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text', 'quiz', 'question_type', 'points', 'order']
    list_filter = ['question_type', 'quiz']
    search_fields = ['question_text']
    list_editable = ['points', 'order']
    inlines = [QuizAnswerInline]
    fieldsets = [
        ('Question', {'fields': ['quiz', 'question_text', 'question_type']}),
        ('Scoring', {'fields': ['points', 'order']}),
    ]


@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = ['answer_text', 'question', 'is_correct']
    list_filter = ['is_correct']
    search_fields = ['answer_text']
    list_editable = ['is_correct']


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['student', 'quiz', 'score', 'is_passed', 'started_at', 'completed_at']
    list_filter = ['is_passed', 'quiz']
    search_fields = ['student__username', 'student__nim', 'quiz__title']
    readonly_fields = ['started_at', 'completed_at']
    inlines = [QuizResponseInline]
    fieldsets = [
        ('Attempt', {'fields': ['quiz', 'student']}),
        ('Results', {'fields': ['score', 'is_passed']}),
        ('Timeline', {'fields': ['started_at', 'completed_at']}),
    ]


@admin.register(QuizResponse)
class QuizResponseAdmin(admin.ModelAdmin):
    list_display = ['attempt', 'question', 'is_correct', 'points_earned']
    list_filter = ['is_correct']
    search_fields = ['attempt__student__username', 'question__question_text']
    readonly_fields = ['attempt', 'question']
    fieldsets = [
        ('Response', {'fields': ['attempt', 'question']}),
        ('Answer', {'fields': ['selected_answer', 'essay_answer']}),
        ('Grading', {'fields': ['is_correct', 'points_earned']}),
    ]
