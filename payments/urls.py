from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.PaymentListView.as_view(), name='list'),
    path('create/', views.PaymentCreateView.as_view(), name='create'),
    path('<int:pk>/', views.PaymentDetailView.as_view(), name='detail'),
    path('<int:pk>/retry/', views.PaymentRetryView.as_view(), name='retry'),
    path('<int:pk>/upload-receipt/', views.PaymentReceiptUploadView.as_view(), name='upload_receipt'),
    path('success/', views.PaymentSuccessView.as_view(), name='success'),
    path('failed/', views.PaymentFailedView.as_view(), name='failed'),

    # Payment gateway callbacks (CSRF exempt)
    path('midtrans/notification/', views.midtrans_notification, name='midtrans_notification'),
    path('xendit/callback/', views.xendit_callback, name='xendit_callback'),
]
