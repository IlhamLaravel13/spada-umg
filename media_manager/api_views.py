from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import MediaFile
from .serializers import MediaFileSerializer, MediaFileUploadSerializer


class MediaFileViewSet(viewsets.ModelViewSet):
    queryset = MediaFile.objects.select_related('uploaded_by').all()
    serializer_class = MediaFileSerializer
    parser_classes = [MultiPartParser, FormParser]
    search_fields = ['title', 'description', 'tags']
    filterset_fields = ['file_type', 'is_public']

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return MediaFileUploadSerializer
        return MediaFileSerializer

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
