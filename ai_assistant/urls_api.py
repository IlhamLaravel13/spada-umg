from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

app_name = 'ai-api'

router = DefaultRouter()
router.register(r'conversations', api_views.AIConversationViewSet, basename='conversation')

urlpatterns = [
    path('', include(router.urls)),
]
