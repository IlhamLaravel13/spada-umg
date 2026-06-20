from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

app_name = 'reports-api'

router = DefaultRouter()
router.register(r'', api_views.ReportViewSet, basename='report')

urlpatterns = [
    path('generate/', api_views.ReportGenerateView.as_view(), name='api-report-generate'),
    path('', include(router.urls)),
]
