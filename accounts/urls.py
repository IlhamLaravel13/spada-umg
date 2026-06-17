from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

    # Registration
    path('register/', views.RegisterView.as_view(), name='register'),
    path('register/mahasiswa/', views.RegisterMahasiswaView.as_view(), name='register_mahasiswa'),
    path('register/dosen/', views.RegisterDosenView.as_view(), name='register_dosen'),

    # Profile
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile_edit'),

    # Password
    path('password-change/', views.PasswordChangeView.as_view(), name='password_change'),
    path('password-reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path(
        'password-reset/confirm/<uidb64>/<token>/',
        views.PasswordResetConfirmView.as_view(),
        name='password_reset_confirm'
    ),
    path(
        'password-reset/complete/',
        views.PasswordResetCompleteView.as_view(),
        name='password_reset_complete'
    ),

    # Email
    path('email/verify/', views.EmailVerificationView.as_view(), name='email_verify'),

    # Sessions
    path('sessions/terminate/<int:session_id>/', views.SessionManagementView.as_view(), name='session_terminate'),
    path('sessions/terminate-all/', views.SessionManagementView.as_view(), name='session_terminate_all'),
]
