from rest_framework import serializers
from .models import AttendanceSession, Attendance


class AttendanceSessionSerializer(serializers.ModelSerializer):
    class_meta_name = serializers.SerializerMethodField()
    course_code = serializers.SerializerMethodField()
    present_count = serializers.SerializerMethodField()
    total_count = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceSession
        fields = '__all__'
        read_only_fields = ['id', 'created_at']

    def get_class_meta_name(self, obj):
        return str(obj.class_meta) if obj.class_meta else None

    def get_course_code(self, obj):
        return obj.class_meta.course.code if obj.class_meta and obj.class_meta.course else None

    def get_present_count(self, obj):
        return obj.attendances.filter(status='present').count()

    def get_total_count(self, obj):
        return obj.attendances.count()


class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    student_nim = serializers.SerializerMethodField()
    session_title = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = '__all__'
        read_only_fields = ['id', 'check_in_time']

    def get_student_name(self, obj):
        return str(obj.student) if obj.student else None

    def get_student_nim(self, obj):
        return obj.student.nim if obj.student else None

    def get_session_title(self, obj):
        return obj.session.title if obj.session else None

    def get_status_display(self, obj):
        return obj.get_status_display()


class AttendanceCheckInSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()
    qr_secret = serializers.CharField(required=False, allow_blank=True)
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class AttendanceReportSerializer(serializers.Serializer):
    class_id = serializers.IntegerField()
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)
