from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView

app_name = 'accounts-api'

urlpatterns = [
    path('login/', TokenObtainPairView.as_view(), name='api-login'),
    path('refresh/', TokenRefreshView.as_view(), name='api-refresh'),
    path('logout/', TokenBlacklistView.as_view(), name='api-logout'),
]
