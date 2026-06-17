from django.urls import path
from . import views

app_name = 'announcements'

urlpatterns = [
    # List & Detail
    path('', views.AnnouncementListView.as_view(), name='announcement_list'),
    path('<int:pk>/', views.AnnouncementDetailView.as_view(), name='announcement_detail'),

    # CRUD
    path('create/', views.AnnouncementCreateView.as_view(), name='announcement_create'),
    path('<int:pk>/update/', views.AnnouncementUpdateView.as_view(), name='announcement_update'),
    path('<int:pk>/delete/', views.AnnouncementDeleteView.as_view(), name='announcement_delete'),

    # Actions
    path('<int:pk>/toggle-publish/', views.AnnouncementTogglePublishView.as_view(), name='announcement_toggle_publish'),
    path('<int:pk>/toggle-important/', views.AnnouncementToggleImportantView.as_view(), name='announcement_toggle_important'),
    path('<int:pk>/mark-read/', views.mark_as_read, name='announcement_mark_read'),

    # Bulk
    path('mark-all-read/', views.mark_all_as_read, name='announcement_mark_all_read'),

    # Banner partial
    path('banner/', views.announcement_banner, name='announcement_banner'),
]
