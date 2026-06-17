from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Material
from .serializers import MaterialSerializer, MaterialUploadSerializer


class MaterialViewSet(viewsets.ModelViewSet):
    queryset = Material.objects.select_related('class_meta', 'uploaded_by').all()
    serializer_class = MaterialSerializer
    search_fields = ['title', 'description']
    filterset_fields = ['class_meta', 'file_type', 'is_published']

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return MaterialUploadSerializer
        return MaterialSerializer

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
