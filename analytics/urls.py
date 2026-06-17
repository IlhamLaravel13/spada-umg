from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('admin/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('dosen/', views.DosenStatsView.as_view(), name='dosen_stats'),
    path('mahasiswa/', views.MahasiswaStatsView.as_view(), name='mahasiswa_stats'),
    path('api/user-stats/', views.get_user_stats_json, name='user_stats_json'),
    path('api/course-stats/', views.get_course_stats_json, name='course_stats_json'),
    path('api/attendance-rate/', views.get_attendance_rate_json, name='attendance_rate_json'),
]
