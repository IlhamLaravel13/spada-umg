from django.urls import path
from . import views

app_name = 'ai_assistant'

urlpatterns = [
    path('', views.AIChatView.as_view(), name='chat'),
    path('send/', views.AISendMessageView.as_view(), name='send_message'),
    path('new/', views.AICreateConversationView.as_view(), name='new_conversation'),
    path('<int:pk>/delete/', views.AIDeleteConversationView.as_view(), name='delete_conversation'),
    path('history/', views.AIHistoryView.as_view(), name='history'),
    path('sidebar/', views.AISidebarView.as_view(), name='sidebar'),
    path('summarize/', views.AISummarizeView.as_view(), name='summarize'),
    path('recommendations/', views.AIRecommendationsView.as_view(), name='recommendations'),
    path('ask/', views.AIAskQuestionView.as_view(), name='ask_question'),
]
