from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from .models import Report
from .serializers import ReportSerializer, ReportGenerateSerializer
from .services import ReportService


class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.select_related('generated_by').all()
    serializer_class = ReportSerializer
    filterset_fields = ['report_type', 'format', 'is_ready']
    search_fields = ['title']

    def perform_create(self, serializer):
        serializer.save(generated_by=self.request.user)


class ReportGenerateView(generics.GenericAPIView):
    serializer_class = ReportGenerateSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = ReportService()
        result = service.generate_report(
            report_type=serializer.validated_data['report_type'],
            fmt=serializer.validated_data.get('format', 'pdf'),
            title=serializer.validated_data.get('title', ''),
            parameters={k: v for k, v in serializer.validated_data.items()
                        if k not in ['report_type', 'format', 'title']},
            user=request.user,
        )

        if result['success']:
            out_serializer = ReportSerializer(result['report'])
            return Response(out_serializer.data, status=status.HTTP_201_CREATED)
        return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)
