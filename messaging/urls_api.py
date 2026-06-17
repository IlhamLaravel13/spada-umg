from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

app_name = 'messaging-api'

router = DefaultRouter()
router.register(r'conversations', api_views.ConversationViewSet, basename='conversation')
router.register(r'messages', api_views.MessageViewSet, basename='message')

urlpatterns = [
    path('', include(router.urls)),
]
