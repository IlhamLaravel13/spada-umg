from rest_framework import serializers
from .models import Faculty, StudyProgram, AcademicYear, Semester, Course, Class, Enrollment


class FacultySerializer(serializers.ModelSerializer):
    study_programs_count = serializers.SerializerMethodField()
    dean_name = serializers.SerializerMethodField()

    class Meta:
        model = Faculty
        fields = '__all__'
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

    def get_study_programs_count(self, obj):
        return obj.study_programs.count()

    def get_dean_name(self, obj):
        return str(obj.dean) if obj.dean else None


class StudyProgramSerializer(serializers.ModelSerializer):
    faculty_name = serializers.SerializerMethodField()
    courses_count = serializers.SerializerMethodField()
    head_name = serializers.SerializerMethodField()

    class Meta:
        model = StudyProgram
        fields = '__all__'
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

    def get_faculty_name(self, obj):
        return obj.faculty.name if obj.faculty else None

    def get_courses_count(self, obj):
        return obj.courses.count()

    def get_head_name(self, obj):
        return str(obj.head) if obj.head else None


class AcademicYearSerializer(serializers.ModelSerializer):
    semesters_count = serializers.SerializerMethodField()

    class Meta:
        model = AcademicYear
        fields = '__all__'
        read_only_fields = ['id', 'created_at']

    def get_semesters_count(self, obj):
        return obj.semesters.count()


class SemesterSerializer(serializers.ModelSerializer):
    academic_year_name = serializers.SerializerMethodField()
    classes_count = serializers.SerializerMethodField()

    class Meta:
        model = Semester
        fields = '__all__'
        read_only_fields = ['id', 'created_at']

    def get_academic_year_name(self, obj):
        return obj.academic_year.year if obj.academic_year else None

    def get_classes_count(self, obj):
        return obj.classes.count()


class CourseSerializer(serializers.ModelSerializer):
    study_program_name = serializers.SerializerMethodField()
    faculty_name = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = '__all__'
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

    def get_study_program_name(self, obj):
        return obj.study_program.name if obj.study_program else None

    def get_faculty_name(self, obj):
        return obj.study_program.faculty.name if obj.study_program and obj.study_program.faculty else None


class ClassSerializer(serializers.ModelSerializer):
    course_name = serializers.SerializerMethodField()
    semester_name = serializers.SerializerMethodField()
    lecturer_name = serializers.SerializerMethodField()
    co_lecturer_name = serializers.SerializerMethodField()
    enrolled_count = serializers.SerializerMethodField()

    class Meta:
        model = Class
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_course_name(self, obj):
        return str(obj.course) if obj.course else None

    def get_semester_name(self, obj):
        return str(obj.semester) if obj.semester else None

    def get_lecturer_name(self, obj):
        return str(obj.lecturer) if obj.lecturer else None

    def get_co_lecturer_name(self, obj):
        return str(obj.co_lecturer) if obj.co_lecturer else None

    def get_enrolled_count(self, obj):
        return obj.enrollments.filter(status='active').count()


class EnrollmentSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    student_nim = serializers.SerializerMethodField()
    class_info = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = '__all__'
        read_only_fields = ['id', 'enrollment_date', 'created_at']

    def get_student_name(self, obj):
        return str(obj.student) if obj.student else None

    def get_student_nim(self, obj):
        return obj.student.nim if obj.student else None

    def get_class_info(self, obj):
        if obj.class_enrolled:
            return str(obj.class_enrolled)
        return None


class EnrollmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ['student', 'class_enrolled']

    def validate(self, data):
        student = data['student']
        class_enrolled = data['class_enrolled']
        if Enrollment.objects.filter(student=student, class_enrolled=class_enrolled).exists():
            raise serializers.ValidationError('Student is already enrolled in this class.')
        active_count = Enrollment.objects.filter(
            student=student, class_enrolled=class_enrolled, status='active'
        ).count()
        if active_count >= class_enrolled.max_students:
            raise serializers.ValidationError('Class is full.')
        return data
