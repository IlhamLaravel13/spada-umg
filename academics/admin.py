from django.contrib import admin
from django.utils.html import format_html
from .models import Faculty, StudyProgram, AcademicYear, Semester, Course, Class, Enrollment

@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'dean_name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'code', 'description']
    prepopulated_fields = {'slug': ['name']}
    list_editable = ['is_active']
    fieldsets = [
        ('Basic Information', {'fields': ['name', 'code', 'slug', 'description']}),
        ('Leadership', {'fields': ['dean']}),
        ('Media', {'fields': ['logo']}),
        ('Status', {'fields': ['is_active']}),
    ]

    def dean_name(self, obj):
        if obj.dean:
            return str(obj.dean)
        return '-'
    dean_name.short_description = 'Dean'

@admin.register(StudyProgram)
class StudyProgramAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'faculty', 'degree', 'head_name', 'is_active']
    list_filter = ['faculty', 'degree', 'is_active']
    search_fields = ['name', 'code', 'description']
    prepopulated_fields = {'slug': ['name']}
    list_editable = ['is_active']
    fieldsets = [
        ('Basic Information', {'fields': ['faculty', 'name', 'code', 'slug', 'degree', 'description']}),
        ('Leadership', {'fields': ['head']}),
        ('Status', {'fields': ['is_active']}),
    ]

    def head_name(self, obj):
        if obj.head:
            return str(obj.head)
        return '-'
    head_name.short_description = 'Head'

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ['year', 'is_active', 'is_even_semester', 'start_date', 'end_date']
    list_filter = ['is_active', 'is_even_semester']
    search_fields = ['year', 'description']
    list_editable = ['is_active']

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ['name', 'academic_year', 'code', 'is_active', 'start_date', 'end_date']
    list_filter = ['academic_year', 'is_active']
    search_fields = ['name', 'code']
    list_editable = ['is_active']
    date_hierarchy = 'start_date'

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'study_program', 'credits', 'semester', 'is_active']
    list_filter = ['study_program__faculty', 'study_program', 'is_active', 'credits']
    search_fields = ['code', 'name', 'description']
    prepopulated_fields = {'slug': ['name']}
    list_editable = ['is_active']
    fieldsets = [
        ('Basic Information', {'fields': ['study_program', 'code', 'name', 'slug', 'description']}),
        ('Academic Details', {'fields': ['credits', 'semester']}),
        ('Status', {'fields': ['is_active']}),
    ]

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'course', 'semester', 'lecturer_name', 'class_type', 'room', 'max_students', 'is_active']
    list_filter = ['class_type', 'is_active', 'semester__academic_year']
    search_fields = ['code', 'name', 'course__name', 'course__code', 'room']
    list_editable = ['is_active']
    filter_horizontal = []
    fieldsets = [
        ('Basic Information', {'fields': ['course', 'semester', 'name', 'code', 'class_type']}),
        ('Schedule', {'fields': ['room', 'schedule', 'meeting_link']}),
        ('Personnel', {'fields': ['lecturer', 'co_lecturer']}),
        ('Capacity', {'fields': ['max_students']}),
        ('Additional', {'fields': ['description', 'is_active']}),
    ]

    def lecturer_name(self, obj):
        if obj.lecturer:
            return str(obj.lecturer)
        return '-'
    lecturer_name.short_description = 'Lecturer'

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'class_enrolled', 'status', 'enrollment_date', 'grade_final', 'grade_letter']
    list_filter = ['status', 'enrollment_date']
    search_fields = ['student__username', 'student__email', 'student__nim', 'class_enrolled__code']
    list_editable = ['status', 'grade_final', 'grade_letter']
    fieldsets = [
        ('Enrollment', {'fields': ['student', 'class_enrolled']}),
        ('Status & Grades', {'fields': ['status', 'grade_final', 'grade_letter']}),
    ]
