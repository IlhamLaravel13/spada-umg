from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.LandingPageView.as_view(), name='landing'),
    path('background/<str:page>/', views.BackgroundImageView.as_view(), name='background_image'),
    path('search/', views.SearchView.as_view(), name='search'),
]
