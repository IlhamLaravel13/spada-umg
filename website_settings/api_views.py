from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import SiteSetting
from .serializers import SiteSettingSerializer, SiteSettingBulkSerializer


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_staff


class SiteSettingViewSet(viewsets.ModelViewSet):
    queryset = SiteSetting.objects.all()
    serializer_class = SiteSettingSerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ['key', 'label', 'value']
    filterset_fields = ['group', 'setting_type', 'is_public']

    @action(detail=False, methods=['get'])
    def public(self, request):
        settings = self.get_queryset().filter(is_public=True)
        data = {s.key: s.value for s in settings}
        return Response(data)

    @action(detail=False, methods=['put'])
    def bulk_update(self, request):
        serializer = SiteSettingBulkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        for key, value in serializer.validated_data['settings'].items():
            SiteSetting.objects.filter(key=key).update(value=value)
        return Response({'status': 'updated'})
