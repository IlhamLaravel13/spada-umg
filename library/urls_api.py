from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

app_name = 'library-api'

router = DefaultRouter()
router.register(r'', api_views.LibraryItemViewSet, basename='library')
router.register(r'categories', api_views.LibraryCategoryViewSet, basename='category')

urlpatterns = [
    path('', include(router.urls)),
]
