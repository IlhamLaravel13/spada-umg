from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('academics/', include('academics.urls')),
    path('courses/', include('courses.urls')),
    path('assignments/', include('assignments.urls')),
    path('quizzes/', include('quizzes.urls')),
    path('attendance/', include('attendance.urls')),
    path('announcements/', include('announcements.urls')),
    path('forum/', include('forum.urls')),
    path('messaging/', include('messaging.urls')),
    path('notifications/', include('notifications.urls')),
    path('analytics/', include('analytics.urls')),
    path('media/', include('media_manager.urls')),
    path('settings/', include('website_settings.urls')),
    path('payments/', include('payments.urls')),
    path('certificates/', include('certificates.urls')),
    path('library/', include('library.urls')),
    path('ai/', include('ai_assistant.urls')),
    path('reports/', include('reports.urls')),
    path('api/', include('api.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Vercel handler
handler404 = 'core.views.handler404'
handler500 = 'core.views.handler500'
