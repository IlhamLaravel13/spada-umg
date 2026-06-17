from rest_framework import serializers
from .models import AnalyticsCache, UserActivity


class AnalyticsCacheSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticsCache
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class UserActivitySerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()

    class Meta:
        model = UserActivity
        fields = '__all__'
        read_only_fields = ['id', 'created_at']

    def get_username(self, obj):
        return obj.user.username if obj.user else None
