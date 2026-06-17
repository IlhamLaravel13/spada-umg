from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardRedirectView.as_view(), name='redirect'),
    path('admin/', views.AdminDashboardView.as_view(), name='admin'),
    path('dosen/', views.DosenDashboardView.as_view(), name='dosen'),
    path('mahasiswa/', views.MahasiswaDashboardView.as_view(), name='mahasiswa'),
]
