from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import F
from .models import LibraryItem, LibraryCategory
from .serializers import LibraryItemSerializer, LibraryItemUploadSerializer, LibraryCategorySerializer


class LibraryCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LibraryCategory.objects.filter(is_active=True)
    serializer_class = LibraryCategorySerializer


class LibraryItemViewSet(viewsets.ModelViewSet):
    serializer_class = LibraryItemSerializer
    search_fields = ['title', 'author', 'description', 'tags', 'publisher']
    filterset_fields = ['item_type', 'category', 'faculty', 'study_program', 'is_published', 'language']

    def get_queryset(self):
        if self.request.user.is_staff:
            return LibraryItem.objects.select_related('category', 'faculty', 'study_program', 'uploaded_by').all()
        return LibraryItem.objects.filter(is_published=True).select_related(
            'category', 'faculty', 'study_program', 'uploaded_by'
        )

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return LibraryItemUploadSerializer
        return LibraryItemSerializer

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

    @action(detail=True, methods=['post'])
    def increment_download(self, request, pk=None):
        item = self.get_object()
        LibraryItem.objects.filter(pk=item.pk).update(download_count=F('download_count') + 1)
        item.refresh_from_db()
        return Response({'download_count': item.download_count})

    @action(detail=True, methods=['post'])
    def increment_view(self, request, pk=None):
        item = self.get_object()
        LibraryItem.objects.filter(pk=item.pk).update(view_count=F('view_count') + 1)
        item.refresh_from_db()
        return Response({'view_count': item.view_count})
