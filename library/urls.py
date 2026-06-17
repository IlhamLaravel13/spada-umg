from django.urls import path
from . import views

app_name = 'library'

urlpatterns = [
    path('', views.LibraryListView.as_view(), name='list'),
    path('<int:pk>/', views.LibraryDetailView.as_view(), name='detail'),
    path('<int:pk>/download/', views.LibraryDownloadView.as_view(), name='download'),
    path('upload/', views.LibraryCreateView.as_view(), name='upload'),
    path('<int:pk>/edit/', views.LibraryUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.LibraryDeleteView.as_view(), name='delete'),
    path('categories/', views.LibraryCategoryListView.as_view(), name='category_list'),
]
