from django.urls import path
from . import views

app_name = 'media_manager'

urlpatterns = [
    path('', views.MediaListView.as_view(), name='media_list'),
    path('upload/', views.MediaUploadView.as_view(), name='media_upload'),
    path('<int:pk>/', views.MediaDetailView.as_view(), name='media_detail'),
    path('<int:pk>/update/', views.MediaUpdateView.as_view(), name='media_update'),
    path('<int:pk>/delete/', views.MediaDeleteView.as_view(), name='media_delete'),
    path('<int:pk>/download/', views.MediaDownloadView.as_view(), name='media_download'),
]
