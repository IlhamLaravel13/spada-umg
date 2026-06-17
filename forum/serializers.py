from rest_framework import serializers
from .models import Forum, ForumTopic, ForumReply


class ForumSerializer(serializers.ModelSerializer):
    class_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    topics_count = serializers.SerializerMethodField()

    class Meta:
        model = Forum
        fields = '__all__'
        read_only_fields = ['id', 'created_at']

    def get_class_name(self, obj):
        return str(obj.class_meta) if obj.class_meta else None

    def get_created_by_name(self, obj):
        return str(obj.created_by) if obj.created_by else None

    def get_topics_count(self, obj):
        return obj.topics.count()


class ForumTopicSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    forum_title = serializers.SerializerMethodField()
    replies_count = serializers.SerializerMethodField()

    class Meta:
        model = ForumTopic
        fields = '__all__'
        read_only_fields = ['id', 'views', 'created_at', 'updated_at']

    def get_author_name(self, obj):
        return str(obj.author)

    def get_forum_title(self, obj):
        return obj.forum.title

    def get_replies_count(self, obj):
        return obj.replies.count()


class ForumReplySerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = ForumReply
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_author_name(self, obj):
        return str(obj.author)

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(id=request.user.id).exists()
        return False


class ForumTopicCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForumTopic
        fields = ['forum', 'title', 'content']


class ForumReplyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForumReply
        fields = ['topic', 'content', 'parent']
