from rest_framework import serializers
from .models import AIProvider, AIConversation, AIMessage


class AIProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIProvider
        fields = ['id', 'name', 'api_key', 'is_active', 'model', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {'api_key': {'write_only': True}}


class AIMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIMessage
        fields = ['id', 'conversation', 'role', 'content', 'metadata', 'created_at']
        read_only_fields = ['id', 'created_at']


class AIConversationSerializer(serializers.ModelSerializer):
    messages = AIMessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = AIConversation
        fields = ['id', 'user', 'title', 'context', 'messages', 'message_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_message_count(self, obj):
        return obj.messages.count()


class AIChatSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=5000)
    conversation_id = serializers.IntegerField(required=False)


class AISummarizeSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=50000)


class AIQuestionSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=5000)
    context = serializers.CharField(required=False, allow_blank=True, max_length=50000)
