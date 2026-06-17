from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    notification_type_display = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'read_at']

    def get_notification_type_display(self, obj):
        return obj.get_notification_type_display()

    def get_time_ago(self, obj):
        from django.utils import timezone
        diff = timezone.now() - obj.created_at
        if diff.days > 0:
            return f"{diff.days} hari yang lalu"
        if diff.seconds >= 3600:
            return f"{diff.seconds // 3600} jam yang lalu"
        if diff.seconds >= 60:
            return f"{diff.seconds // 60} menit yang lalu"
        return "baru saja"


class NotificationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['recipient', 'notification_type', 'title', 'message', 'link', 'is_important']


class NotificationBulkCreateSerializer(serializers.Serializer):
    notifications = NotificationCreateSerializer(many=True)
