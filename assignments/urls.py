from django.urls import path
from . import views

app_name = 'assignments'

urlpatterns = [
    path('', views.AssignmentListView.as_view(), name='assignment_list'),
    path('create/', views.AssignmentCreateView.as_view(), name='assignment_create'),
    path('<int:pk>/', views.AssignmentDetailView.as_view(), name='assignment_detail'),
    path('<int:pk>/update/', views.AssignmentUpdateView.as_view(), name='assignment_update'),
    path('<int:pk>/delete/', views.AssignmentDeleteView.as_view(), name='assignment_delete'),
    path('<int:pk>/submit/', views.AssignmentSubmitView.as_view(), name='assignment_submit'),
    path('<int:pk>/submissions/', views.SubmissionListView.as_view(), name='submission_list'),
    path('submissions/<int:submission_pk>/grade/', views.AssignmentGradeView.as_view(), name='assignment_grade'),
    path('submissions/', views.SubmissionListView.as_view(), name='submission_list_all'),
    path('load-assignments/', views.load_assignments, name='load_assignments'),
]
