from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

app_name = 'notifications-api'

router = DefaultRouter()
router.register(r'', api_views.NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
]
