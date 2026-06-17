from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

app_name = 'forums-api'

router = DefaultRouter()
router.register(r'', api_views.ForumViewSet)
router.register(r'topics', api_views.ForumTopicViewSet, basename='topic')
router.register(r'replies', api_views.ForumReplyViewSet, basename='reply')

urlpatterns = [
    path('', include(router.urls)),
]
