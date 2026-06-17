from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from .models import Report
from .serializers import ReportSerializer, ReportGenerateSerializer
from .services import ReportService


class ReportListCreateAPIView(generics.ListCreateAPIView):
    queryset = Report.objects.select_related('generated_by').all()
    serializer_class = ReportSerializer
    filterset_fields = ['report_type', 'format', 'is_ready']
    search_fields = ['title']
    ordering_fields = ['-created_at']

    def perform_create(self, serializer):
        serializer.save(generated_by=self.request.user)


class ReportDetailAPIView(generics.RetrieveDestroyAPIView):
    queryset = Report.objects.select_related('generated_by').all()
    serializer_class = ReportSerializer

    def perform_destroy(self, instance):
        if instance.file:
            instance.file.delete(save=False)
        instance.delete()


class ReportGenerateAPIView(generics.GenericAPIView):
    serializer_class = ReportGenerateSerializer
    parser_classes = [JSONParser]

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
