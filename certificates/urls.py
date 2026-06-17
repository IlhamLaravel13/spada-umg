from django.urls import path
from . import views

app_name = 'certificates'

urlpatterns = [
    path('', views.CertificateListView.as_view(), name='list'),
    path('<int:pk>/', views.CertificateDetailView.as_view(), name='detail'),
    path('<int:pk>/download/', views.CertificateDownloadView.as_view(), name='download'),
    path('verify/', views.CertificateVerifyView.as_view(), name='verify'),
    path('verify/result/', views.CertificateVerifyResultView.as_view(), name='verify_result'),
    path('request/', views.CertificateRequestView.as_view(), name='request'),
]
