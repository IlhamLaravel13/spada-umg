from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

app_name = 'certificates-api'

router = DefaultRouter()
router.register(r'', api_views.CertificateViewSet, basename='certificate')

urlpatterns = [
    path('', include(router.urls)),
]
