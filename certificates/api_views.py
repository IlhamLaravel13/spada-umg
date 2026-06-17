from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Certificate
from .serializers import CertificateSerializer, CertificateCreateSerializer, CertificateVerifySerializer


class CertificateViewSet(viewsets.ModelViewSet):
    serializer_class = CertificateSerializer
    search_fields = ['title', 'certificate_number']
    filterset_fields = ['certificate_type', 'is_verified']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Certificate.objects.select_related('user', 'template').all()
        return Certificate.objects.filter(user=user).select_related('user', 'template')

    def get_serializer_class(self):
        if self.action == 'create':
            return CertificateCreateSerializer
        return CertificateSerializer

    @action(detail=False, methods=['post'])
    def verify(self, request):
        serializer = CertificateVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cert = Certificate.objects.get(
            certificate_number=serializer.validated_data['certificate_number']
        )
        out = CertificateSerializer(cert)
        return Response(out.data)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        certificate = self.get_object()
        if certificate.pdf_file:
            return Response({'download_url': certificate.pdf_file.url})
        return Response({'error': 'File not available'}, status=status.HTTP_404_NOT_FOUND)
