from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.InboxView.as_view(), name='inbox'),
    path('list/', views.ConversationListView.as_view(), name='conversation_list'),
    path('<int:pk>/', views.ConversationDetailView.as_view(), name='conversation_detail'),
    path('new/', views.StartConversationView.as_view(), name='start_conversation'),
    path('<int:pk>/send/', views.SendMessageView.as_view(), name='send_message'),
    path('message/<int:pk>/read/', views.MarkAsReadView.as_view(), name='mark_read'),
    path('unread-count/', views.UnreadCountView.as_view(), name='unread_count'),
]
