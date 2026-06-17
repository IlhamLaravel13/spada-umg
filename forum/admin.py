from django.contrib import admin
from django.utils.html import format_html
from .models import Forum, ForumTopic, ForumReply


@admin.register(Forum)
class ForumAdmin(admin.ModelAdmin):
    list_display = ['title', 'class_meta', 'is_active', 'created_by', 'created_at', 'topics_count']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description', 'class_meta__name']
    list_editable = ['is_active']
    date_hierarchy = 'created_at'
    fieldsets = [
        ('Content', {'fields': ['title', 'description', 'class_meta']}),
        ('Status', {'fields': ['is_active', 'created_by']}),
    ]
    readonly_fields = ['created_at']

    def topics_count(self, obj):
        count = obj.topics.count()
        return format_html('<span class="badge">{}</span>', count)
    topics_count.short_description = 'Topics'


@admin.register(ForumTopic)
class ForumTopicAdmin(admin.ModelAdmin):
    list_display = ['title', 'forum', 'author', 'is_pinned', 'is_closed', 'views', 'created_at', 'replies_count']
    list_filter = ['is_pinned', 'is_closed', 'created_at']
    search_fields = ['title', 'content', 'author__username']
    list_editable = ['is_pinned', 'is_closed']
    date_hierarchy = 'created_at'
    fieldsets = [
        ('Content', {'fields': ['forum', 'title', 'content']}),
        ('Status', {'fields': ['author', 'is_pinned', 'is_closed']}),
    ]
    readonly_fields = ['views', 'created_at', 'updated_at']

    def replies_count(self, obj):
        count = obj.replies.count()
        return format_html('<span class="badge">{}</span>', count)
    replies_count.short_description = 'Replies'


@admin.register(ForumReply)
class ForumReplyAdmin(admin.ModelAdmin):
    list_display = ['short_content', 'topic', 'author', 'is_solution', 'created_at', 'likes_count']
    list_filter = ['is_solution', 'created_at']
    search_fields = ['content', 'author__username', 'topic__title']
    list_editable = ['is_solution']
    date_hierarchy = 'created_at'
    fieldsets = [
        ('Content', {'fields': ['topic', 'content', 'parent', 'author']}),
        ('Status', {'fields': ['is_solution']}),
    ]
    readonly_fields = ['created_at', 'updated_at']

    def short_content(self, obj):
        return obj.content[:75] + '...' if len(obj.content) > 75 else obj.content
    short_content.short_description = 'Content'

    def likes_count(self, obj):
        count = obj.likes.count()
        return format_html('<span class="badge">{}</span>', count)
    likes_count.short_description = 'Likes'
