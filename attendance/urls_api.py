from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

app_name = 'attendance-api'

router = DefaultRouter()
router.register(r'sessions', api_views.AttendanceSessionViewSet, basename='session')
router.register(r'records', api_views.AttendanceViewSet, basename='attendance')

urlpatterns = [
    path('', include(router.urls)),
]
