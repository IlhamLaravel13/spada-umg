from django.urls import path
from . import views
from . import api

app_name = 'reports'

urlpatterns = [
    path('', views.ReportListView.as_view(), name='list'),
    path('generate/', views.ReportGenerateView.as_view(), name='generate'),
    path('<int:pk>/', views.ReportDetailView.as_view(), name='detail'),
    path('<int:pk>/delete/', views.ReportDeleteView.as_view(), name='delete'),
    path('<int:pk>/download/', views.ReportDownloadView.as_view(), name='download'),
]

url_api = [
    path('', api.ReportListCreateAPIView.as_view(), name='api-list'),
    path('<int:pk>/', api.ReportDetailAPIView.as_view(), name='api-detail'),
    path('generate/', api.ReportGenerateAPIView.as_view(), name='api-generate'),
]

urlpatterns_api = url_api
