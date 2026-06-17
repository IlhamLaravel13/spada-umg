from django.urls import path
from . import views

app_name = 'website_settings'

urlpatterns = [
    path('', views.SettingsListView.as_view(), name='settings_list'),
    path('group/<str:group>/', views.SettingsGroupPartialView.as_view(), name='settings_group_partial'),
    path('bulk-update/', views.SettingsBulkUpdateView.as_view(), name='settings_bulk_update'),
    path('create/', views.SettingCreateView.as_view(), name='setting_create'),
    path('<int:pk>/update/', views.SettingUpdateView.as_view(), name='setting_update'),
    path('<int:pk>/delete/', views.SettingDeleteView.as_view(), name='setting_delete'),
]
