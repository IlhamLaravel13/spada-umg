from django.urls import path
from . import api_views

app_name = 'analytics-api'

urlpatterns = [
    path('dashboard/', api_views.DashboardStatsView.as_view(), name='api-dashboard-stats'),
    path('academic/', api_views.AcademicStatsView.as_view(), name='api-academic-stats'),
    path('activities/', api_views.UserActivityStatsView.as_view(), name='api-user-activities'),
]
