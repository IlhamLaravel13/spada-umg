from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

app_name = 'settings-api'

router = DefaultRouter()
router.register(r'', api_views.SiteSettingViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
