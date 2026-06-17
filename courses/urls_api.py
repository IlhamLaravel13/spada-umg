from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

app_name = 'materials-api'

router = DefaultRouter()
router.register(r'', api_views.MaterialViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
