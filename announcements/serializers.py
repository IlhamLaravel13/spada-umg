from rest_framework import serializers
from .models import Announcement, AnnouncementRead


class AnnouncementSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()
    target_class_name = serializers.SerializerMethodField()
    category_display = serializers.SerializerMethodField()
    audience_display = serializers.SerializerMethodField()
    is_read = serializers.SerializerMethodField()
    reads_count = serializers.SerializerMethodField()

    class Meta:
        model = Announcement
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_created_by_name(self, obj):
        return str(obj.created_by) if obj.created_by else None

    def get_target_class_name(self, obj):
        return str(obj.target_class) if obj.target_class else None

    def get_category_display(self, obj):
        return obj.get_category_display()

    def get_audience_display(self, obj):
        return obj.get_audience_display()

    def get_is_read(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.reads.filter(user=request.user).exists()
        return False

    def get_reads_count(self, obj):
        return obj.reads.count()


class AnnouncementReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnnouncementRead
        fields = '__all__'
        read_only_fields = ['id', 'read_at']


class AnnouncementCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = [
            'title', 'content', 'category', 'audience', 'target_class',
            'is_important', 'is_published', 'attachment', 'pinned_until',
        ]
