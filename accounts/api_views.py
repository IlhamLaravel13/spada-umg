from rest_framework import viewsets, generics, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User
from .serializers import UserSerializer, ProfileSerializer


class IsAdminOrSelf(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or request.user.is_superuser or obj == request.user


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    search_fields = ['username', 'email', 'first_name', 'last_name', 'nim', 'nidn']
    filterset_fields = ['role', 'is_active', 'faculty', 'study_program']

    def get_permissions(self):
        if self.action in ('list', 'create', 'destroy'):
            return [permissions.IsAdminUser()]
        elif self.action in ('retrieve', 'update', 'partial_update'):
            return [permissions.IsAuthenticated(), IsAdminOrSelf()]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=['get', 'put'])
    def me(self, request):
        if request.method == 'GET':
            serializer = UserSerializer(request.user)
            return Response(serializer.data)
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)
