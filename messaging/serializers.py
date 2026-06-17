from rest_framework import serializers
from .models import Conversation, Message


class ConversationSerializer(serializers.ModelSerializer):
    participants_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    participant_names = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_participants_count(self, obj):
        return obj.participants.count()

    def get_last_message(self, obj):
        messages = getattr(obj, 'last_message', None)
        if messages:
            msg = messages[0]
            return {
                'id': msg.id,
                'sender_name': str(msg.sender),
                'body': msg.body[:100],
                'created_at': msg.created_at.isoformat(),
                'is_read': msg.is_read,
            }
        return None

    def get_unread_count(self, obj):
        return getattr(obj, 'unread_count', 0)

    def get_participant_names(self, obj):
        return [str(u) for u in obj.participants.all()]


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    sender_avatar = serializers.SerializerMethodField()
    sender_role = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = '__all__'
        read_only_fields = ['id', 'created_at']

    def get_sender_name(self, obj):
        return str(obj.sender)

    def get_sender_avatar(self, obj):
        if obj.sender.avatar:
            return obj.sender.avatar.url
        return None

    def get_sender_role(self, obj):
        return obj.sender.role


class MessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['conversation', 'body', 'attachment']
