from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # Mahasiswa
    path('', views.CourseListView.as_view(), name='course_list'),
    path('<int:pk>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('<int:class_id>/materials/', views.MaterialListView.as_view(), name='material_list'),
    path('materials/<int:pk>/', views.MaterialDetailView.as_view(), name='material_detail'),

    # Dosen
    path('my-courses/', views.MyCoursesView.as_view(), name='my_courses'),
    path('<int:class_id>/materials/manage/', views.MaterialManageView.as_view(), name='material_manage'),
    path('<int:class_id>/materials/upload/', views.MaterialUploadView.as_view(), name='material_upload'),
    path('materials/<int:pk>/edit/', views.MaterialUpdateView.as_view(), name='material_edit'),
    path('materials/<int:pk>/delete/', views.MaterialDeleteView.as_view(), name='material_delete'),
    path('materials/<int:pk>/toggle-publish/', views.MaterialTogglePublishView.as_view(), name='material_toggle_publish'),

    # Progress
    path('<int:class_id>/materials/<int:material_id>/complete/', views.MarkCompleteView.as_view(), name='mark_complete'),
    path('<int:class_id>/materials/<int:material_id>/incomplete/', views.MarkIncompleteView.as_view(), name='mark_incomplete'),

    # Comments
    path('materials/<int:pk>/comments/', views.MaterialCommentView.as_view(), name='material_comment'),
]
