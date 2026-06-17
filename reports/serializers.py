from rest_framework import serializers
from .models import Report

class ReportSerializer(serializers.ModelSerializer):
    generated_by_name = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = [
            'id', 'title', 'report_type', 'format', 'parameters',
            'generated_by', 'generated_by_name', 'file', 'download_url',
            'is_ready', 'created_at',
        ]
        read_only_fields = ['id', 'generated_by', 'is_ready', 'created_at', 'file']

    def get_generated_by_name(self, obj):
        if obj.generated_by:
            return obj.generated_by.get_full_name() or obj.generated_by.username
        return None

    def get_download_url(self, obj):
        if obj.file:
            return obj.file.url
        return None

class ReportGenerateSerializer(serializers.Serializer):
    report_type = serializers.ChoiceField(choices=Report.TYPE_CHOICES)
    format = serializers.ChoiceField(choices=Report.FORMAT_CHOICES, default='pdf')
    title = serializers.CharField(max_length=200)
    semester_id = serializers.IntegerField(required=False, allow_null=True)
    class_id = serializers.IntegerField(required=False, allow_null=True)
    course_id = serializers.IntegerField(required=False, allow_null=True)
    faculty_id = serializers.IntegerField(required=False, allow_null=True)
    study_program_id = serializers.IntegerField(required=False, allow_null=True)
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    academic_year_id = serializers.IntegerField(required=False, allow_null=True)
    status = serializers.CharField(required=False, allow_null=True)
