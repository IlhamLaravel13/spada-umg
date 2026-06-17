from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Payment
from .serializers import PaymentSerializer, PaymentCreateSerializer, PaymentConfirmSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    search_fields = ['invoice_number', 'description']
    filterset_fields = ['payment_type', 'status', 'payment_method']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Payment.objects.select_related('user').all()
        return Payment.objects.filter(user=user).select_related('user')

    def get_serializer_class(self):
        if self.action == 'create':
            return PaymentCreateSerializer
        return PaymentSerializer

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        payment = self.get_object()
        serializer = PaymentConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment.transaction_id = serializer.validated_data['transaction_id']
        payment.status = serializer.validated_data['status']
        if serializer.validated_data.get('payment_method'):
            payment.payment_method = serializer.validated_data['payment_method']
        if payment.status == 'success':
            from django.utils import timezone
            payment.paid_at = timezone.now()
        payment.save()
        return Response(PaymentSerializer(payment).data)
