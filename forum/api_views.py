from django.db import models
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Forum, ForumTopic, ForumReply
from .serializers import (
    ForumSerializer, ForumTopicSerializer, ForumTopicCreateSerializer,
    ForumReplySerializer, ForumReplyCreateSerializer,
)


class ForumViewSet(viewsets.ModelViewSet):
    queryset = Forum.objects.select_related('class_meta', 'created_by').all()
    serializer_class = ForumSerializer
    filterset_fields = ['class_meta', 'is_active']


class ForumTopicViewSet(viewsets.ModelViewSet):
    queryset = ForumTopic.objects.select_related('forum', 'author').all()
    serializer_class = ForumTopicSerializer
    search_fields = ['title', 'content']
    filterset_fields = ['forum', 'is_pinned', 'is_closed']

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ForumTopicCreateSerializer
        return ForumTopicSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'])
    def increment_views(self, request, pk=None):
        topic = self.get_object()
        ForumTopic.objects.filter(pk=topic.pk).update(views=models.F('views') + 1)
        return Response({'views': topic.views + 1})


class ForumReplyViewSet(viewsets.ModelViewSet):
    queryset = ForumReply.objects.select_related('topic', 'author', 'parent').all()
    serializer_class = ForumReplySerializer
    filterset_fields = ['topic', 'is_solution']

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ForumReplyCreateSerializer
        return ForumReplySerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'])
    def toggle_like(self, request, pk=None):
        reply = self.get_object()
        if reply.likes.filter(id=request.user.id).exists():
            reply.likes.remove(request.user)
            liked = False
        else:
            reply.likes.add(request.user)
            liked = True
        return Response({'liked': liked, 'likes_count': reply.likes.count()})
