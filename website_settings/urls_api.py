from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

app_name = 'settings-api'

router = DefaultRouter()
router.register(r'', api_views.SiteSettingViewSet, basename='site-setting')

urlpatterns = [
    path('', include(router.urls)),
]
