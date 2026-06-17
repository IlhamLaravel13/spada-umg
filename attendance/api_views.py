from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import AttendanceSession, Attendance
from .serializers import (
    AttendanceSessionSerializer, AttendanceSerializer,
    AttendanceCheckInSerializer,
)
from .services import AttendanceService
from django.utils import timezone


class AttendanceSessionViewSet(viewsets.ModelViewSet):
    queryset = AttendanceSession.objects.select_related('class_meta', 'created_by').all()
    serializer_class = AttendanceSessionSerializer
    filterset_fields = ['class_meta', 'is_active']
    search_fields = ['title', 'topic']


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.select_related('session', 'student', 'verified_by').all()
    serializer_class = AttendanceSerializer
    filterset_fields = ['session', 'student', 'status']

    @action(detail=False, methods=['post'])
    def check_in(self, request, *args, **kwargs):
        serializer = AttendanceCheckInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = AttendanceService()
        result = service.check_in(
            session_id=serializer.validated_data['session_id'],
            student=request.user,
            qr_secret=serializer.validated_data.get('qr_secret', ''),
            latitude=serializer.validated_data.get('latitude'),
            longitude=serializer.validated_data.get('longitude'),
            notes=serializer.validated_data.get('notes', ''),
        )
        if result['success']:
            return Response(result['data'], status=status.HTTP_201_CREATED)
        return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)
