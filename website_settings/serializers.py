from rest_framework import serializers
from .models import SiteSetting


class SiteSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSetting
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class SiteSettingBulkSerializer(serializers.Serializer):
    settings = serializers.DictField(child=serializers.CharField(), allow_empty=True)
