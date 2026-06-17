from rest_framework import serializers
from .models import Assignment, AssignmentSubmission, AssignmentSubmissionAttachment


class AssignmentSubmissionAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssignmentSubmissionAttachment
        fields = '__all__'
        read_only_fields = ['id', 'uploaded_at']


class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    student_nim = serializers.SerializerMethodField()
    grader_name = serializers.SerializerMethodField()
    attachments = AssignmentSubmissionAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = AssignmentSubmission
        fields = '__all__'
        read_only_fields = ['id', 'submitted_at', 'graded_at']

    def get_student_name(self, obj):
        return str(obj.student) if obj.student else None

    def get_student_nim(self, obj):
        return obj.student.nim if obj.student else None

    def get_grader_name(self, obj):
        return str(obj.graded_by) if obj.graded_by else None


class AssignmentSubmissionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssignmentSubmission
        fields = ['assignment', 'file', 'notes']

    def validate(self, data):
        assignment = data['assignment']
        if not assignment.is_published:
            raise serializers.ValidationError('Assignment is not open for submissions')
        if not assignment.allow_late_submission and assignment.is_past_due():
            raise serializers.ValidationError('Due date has passed')
        return data


class AssignmentSerializer(serializers.ModelSerializer):
    submissions_count = serializers.SerializerMethodField()
    graded_count = serializers.SerializerMethodField()
    class_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_submissions_count(self, obj):
        return obj.submissions.count()

    def get_graded_count(self, obj):
        return obj.submissions.filter(score__isnull=False).count()

    def get_class_name(self, obj):
        return str(obj.class_meta) if obj.class_meta else None

    def get_created_by_name(self, obj):
        return str(obj.created_by) if obj.created_by else None
