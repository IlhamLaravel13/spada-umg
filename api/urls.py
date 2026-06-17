from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.api_root, name='api-root'),

    # Auth APIs
    path('auth/', include('accounts.urls_api')),

    # Core APIs
    path('users/', include('accounts.urls_api_users')),

    # Academics APIs
    path('faculties/', include('academics.urls_api_faculties')),
    path('study-programs/', include('academics.urls_api_programs')),
    path('courses/', include('academics.urls_api_courses')),
    path('classes/', include('academics.urls_api_classes')),
    path('semesters/', include('academics.urls_api_semesters')),
    path('enrollments/', include('academics.urls_api_enrollments')),
    path('academic-years/', include('academics.urls_api_academic_years')),

    # Course APIs
    path('materials/', include('courses.urls_api')),

    # Assignment APIs
    path('assignments/', include('assignments.urls_api')),

    # Quiz APIs
    path('quizzes/', include('quizzes.urls_api')),

    # Attendance APIs
    path('attendance/', include('attendance.urls_api')),

    # Announcement APIs
    path('announcements/', include('announcements.urls_api')),

    # Forum APIs
    path('forums/', include('forum.urls_api')),

    # Messaging APIs
    path('messages/', include('messaging.urls_api')),

    # Notification APIs
    path('notifications/', include('notifications.urls_api')),

    # Analytics APIs
    path('analytics/', include('analytics.urls_api')),

    # Media APIs
    path('media/', include('media_manager.urls_api')),

    # Settings APIs
    path('settings/', include('website_settings.urls_api')),

    # Payment APIs
    path('payments/', include('payments.urls_api')),

    # Certificate APIs
    path('certificates/', include('certificates.urls_api')),

    # Library APIs
    path('library/', include('library.urls_api')),

    # AI APIs
    path('ai/', include('ai_assistant.urls_api')),

    # Reports APIs
    path('reports/', include('reports.urls_api')),

    # System
    path('health/', include('api.health_urls')),
]
