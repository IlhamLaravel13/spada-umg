from rest_framework import serializers
from .models import Material, MaterialComment, CourseProgress


class MaterialSerializer(serializers.ModelSerializer):
    class_name = serializers.SerializerMethodField()
    uploaded_by_name = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()
    file_type_icon = serializers.SerializerMethodField()

    class Meta:
        model = Material
        fields = [
            'id', 'class_meta', 'class_name', 'title', 'description',
            'file_type', 'file_type_icon', 'file', 'file_url', 'file_size',
            'is_published', 'allow_download', 'order', 'uploaded_by',
            'uploaded_by_name', 'download_url', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'uploaded_by', 'created_at', 'updated_at', 'file_size']

    def get_class_name(self, obj):
        return str(obj.class_meta)

    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by:
            return obj.uploaded_by.get_full_name() or obj.uploaded_by.username
        return None

    def get_download_url(self, obj):
        if obj.file:
            return obj.file.url
        if obj.file_url:
            return obj.file_url
        return None

    def get_file_type_icon(self, obj):
        icons = {
            'pdf': 'fa-file-pdf',
            'docx': 'fa-file-word',
            'pptx': 'fa-file-powerpoint',
            'xlsx': 'fa-file-excel',
            'video': 'fa-file-video',
            'audio': 'fa-file-audio',
            'image': 'fa-file-image',
            'archive': 'fa-file-archive',
            'link': 'fa-link',
            'other': 'fa-file',
        }
        return icons.get(obj.file_type, 'fa-file')


class MaterialCommentSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    user_avatar = serializers.SerializerMethodField()

    class Meta:
        model = MaterialComment
        fields = ['id', 'material', 'user', 'user_name', 'user_avatar', 'comment', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def get_user_avatar(self, obj):
        if obj.user.avatar:
            return obj.user.avatar.url
        return None


class CourseProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseProgress
        fields = ['id', 'student', 'class_meta', 'material', 'is_completed', 'completed_at']
        read_only_fields = ['id', 'completed_at']


class MaterialUploadSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    file_type = serializers.ChoiceField(choices=Material.TYPE_CHOICES)
    file = serializers.FileField(required=False)
    file_url = serializers.URLField(required=False, allow_blank=True)
    is_published = serializers.BooleanField(default=True)
    allow_download = serializers.BooleanField(default=True)
    order = serializers.IntegerField(default=0)

    def validate(self, data):
        if not data.get('file') and not data.get('file_url'):
            raise serializers.ValidationError('File atau URL harus diisi')
        return data
