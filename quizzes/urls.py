from django.urls import path
from . import views

app_name = 'quizzes'

urlpatterns = [
    path('', views.QuizListView.as_view(), name='quiz_list'),
    path('create/', views.QuizCreateView.as_view(), name='quiz_create'),
    path('<int:pk>/', views.QuizDetailView.as_view(), name='quiz_detail'),
    path('<int:pk>/update/', views.QuizUpdateView.as_view(), name='quiz_update'),
    path('<int:pk>/delete/', views.QuizDeleteView.as_view(), name='quiz_delete'),
    path('<int:pk>/take/', views.QuizTakeView.as_view(), name='quiz_take'),
    path('<int:pk>/submit/', views.QuizSubmitView.as_view(), name='quiz_submit'),
    path('<int:pk>/result/<int:attempt_pk>/', views.QuizResultView.as_view(), name='quiz_result'),
    path('<int:pk>/questions/create/', views.QuestionCreateView.as_view(), name='question_create'),
    path('questions/<int:pk>/update/', views.QuestionUpdateView.as_view(), name='question_update'),
    path('questions/<int:pk>/delete/', views.QuestionDeleteView.as_view(), name='question_delete'),
    path('grades/', views.QuizGradeListView.as_view(), name='quiz_grades'),
    path('grades/<int:attempt_pk>/essay/<int:question_pk>/grade/', views.QuizGradeEssayView.as_view(), name='quiz_grade_essay'),
    path('load-quizzes/', views.load_quizzes, name='load_quizzes'),
]
