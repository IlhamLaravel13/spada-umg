from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

app_name = 'assignments-api'

router = DefaultRouter()
router.register(r'', api_views.AssignmentViewSet)
router.register(r'submissions', api_views.SubmissionViewSet, basename='submission')

urlpatterns = [
    path('', include(router.urls)),
]
