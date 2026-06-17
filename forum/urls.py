from django.urls import path
from . import views

app_name = 'forum'

urlpatterns = [
    # Forums
    path('', views.ForumListView.as_view(), name='forum_list'),
    path('class/<int:class_id>/', views.ClassForumListView.as_view(), name='class_forum_list'),
    path('<int:pk>/', views.ForumDetailView.as_view(), name='forum_detail'),
    path('create/', views.ForumCreateView.as_view(), name='forum_create'),

    # Topics
    path('topic/<int:pk>/', views.TopicDetailView.as_view(), name='topic_detail'),
    path('<int:forum_id>/topic/create/', views.TopicCreateView.as_view(), name='topic_create'),
    path('topic/<int:pk>/update/', views.TopicUpdateView.as_view(), name='topic_update'),
    path('topic/<int:pk>/delete/', views.TopicDeleteView.as_view(), name='topic_delete'),
    path('topic/<int:pk>/toggle-pin/', views.ToggleTopicPinView.as_view(), name='topic_toggle_pin'),
    path('topic/<int:pk>/toggle-close/', views.ToggleTopicCloseView.as_view(), name='topic_toggle_close'),

    # Replies
    path('topic/<int:topic_id>/reply/', views.ReplyCreateView.as_view(), name='reply_create'),
    path('reply/<int:pk>/update/', views.ReplyUpdateView.as_view(), name='reply_update'),
    path('reply/<int:pk>/delete/', views.ReplyDeleteView.as_view(), name='reply_delete'),
    path('reply/<int:pk>/like/', views.ReplyToggleLikeView.as_view(), name='reply_toggle_like'),
    path('reply/<int:pk>/solution/<int:topic_id>/', views.ReplyMarkSolutionView.as_view(), name='reply_mark_solution'),
]
