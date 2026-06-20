from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

app_name = 'quizzes-api'

router = DefaultRouter()
router.register(r'', api_views.QuizViewSet, basename='quiz')
router.register(r'questions', api_views.QuizQuestionViewSet, basename='question')
router.register(r'attempts', api_views.QuizAttemptViewSet, basename='attempt')

urlpatterns = [
    path('', include(router.urls)),
]
