from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Announcement, AnnouncementRead
from .serializers import AnnouncementSerializer, AnnouncementCreateSerializer, AnnouncementReadSerializer


class AnnouncementViewSet(viewsets.ModelViewSet):
    queryset = Announcement.objects.select_related('created_by', 'target_class').all()
    serializer_class = AnnouncementSerializer
    search_fields = ['title', 'content']
    filterset_fields = ['category', 'audience', 'is_published', 'is_important']

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return AnnouncementCreateSerializer
        return AnnouncementSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        announcement = self.get_object()
        AnnouncementRead.objects.get_or_create(
            announcement=announcement, user=request.user
        )
        return Response({'status': 'read'})
