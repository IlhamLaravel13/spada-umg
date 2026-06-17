from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # Sessions
    path('sessions/', views.SessionListView.as_view(), name='session_list'),
    path('sessions/create/', views.SessionCreateView.as_view(), name='session_create'),
    path('sessions/<int:pk>/', views.SessionDetailView.as_view(), name='session_detail'),
    path('sessions/<int:pk>/update/', views.SessionUpdateView.as_view(), name='session_update'),
    path('sessions/<int:pk>/delete/', views.SessionDeleteView.as_view(), name='session_delete'),
    path('sessions/<int:pk>/toggle-active/', views.SessionToggleActiveView.as_view(), name='session_toggle_active'),

    # Take attendance
    path('sessions/<int:pk>/take/', views.take_attendance, name='take_attendance'),
    path('sessions/<int:pk>/manual-checkin/', views.ManualCheckInView.as_view(), name='manual_checkin'),
    path('sessions/<int:pk>/qr-checkin/', views.check_in_qr, name='qr_checkin'),

    # Attendance records
    path('attendance/<int:pk>/update-status/', views.UpdateAttendanceStatusView.as_view(), name='update_attendance_status'),

    # Reports
    path('reports/', views.AttendanceReportView.as_view(), name='attendance_report'),

    # My attendance (mahasiswa)
    path('my-attendance/', views.MyAttendanceView.as_view(), name='my_attendance'),
]
