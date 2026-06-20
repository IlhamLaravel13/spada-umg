from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

app_name = 'payments-api'

router = DefaultRouter()
router.register(r'', api_views.PaymentViewSet, basename='payments')

urlpatterns = [
    path('', include(router.urls)),
]
