from django.db.models import QuerySet, Q, Sum
from django.utils import timezone
from .models import Payment, PaymentReceipt


class PaymentRepository:
    def get_by_id(self, payment_id: int) -> Payment | None:
        return Payment.objects.filter(id=payment_id).first()

    def get_by_invoice(self, invoice_number: str) -> Payment | None:
        return Payment.objects.filter(invoice_number=invoice_number).first()

    def get_by_transaction(self, transaction_id: str) -> Payment | None:
        return Payment.objects.filter(transaction_id=transaction_id).first()

    def get_user_payments(self, user_id: int) -> QuerySet[Payment]:
        return Payment.objects.filter(user_id=user_id)

    def get_by_status(self, status: str) -> QuerySet[Payment]:
        return Payment.objects.filter(status=status)

    def get_pending_expired(self) -> QuerySet[Payment]:
        return Payment.objects.filter(
            status='pending', expired_at__lt=timezone.now()
        )

    def get_successful(self) -> QuerySet[Payment]:
        return Payment.objects.filter(status='success')

    def get_user_payments_by_type(self, user_id: int, payment_type: str) -> QuerySet[Payment]:
        return Payment.objects.filter(user_id=user_id, payment_type=payment_type)

    def search(self, query: str) -> QuerySet[Payment]:
        return Payment.objects.filter(
            Q(invoice_number__icontains=query) |
            Q(transaction_id__icontains=query) |
            Q(user__username__icontains=query) |
            Q(user__email__icontains=query) |
            Q(user__nim__icontains=query) |
            Q(description__icontains=query)
        )

    def create_payment(self, **kwargs) -> Payment:
        return Payment.objects.create(**kwargs)

    def update_payment(self, payment_id: int, **kwargs) -> Payment | None:
        updated = Payment.objects.filter(id=payment_id).update(**kwargs)
        if updated:
            return self.get_by_id(payment_id)
        return None

    def update_status(self, payment_id: int, status: str, **extra) -> Payment | None:
        update_data = {'status': status, **extra}
        return self.update_payment(payment_id, **update_data)

    def mark_success(self, payment_id: int, transaction_id: str = '',
                     payment_method: str = '') -> Payment | None:
        return self.update_payment(payment_id, **{
            'status': 'success',
            'transaction_id': transaction_id or None,
            'payment_method': payment_method or None,
            'paid_at': timezone.now(),
        })

    def count_by_status(self) -> dict:
        return {
            status: Payment.objects.filter(status=status).count()
            for status, _ in Payment.STATUS_CHOICES
        }

    def total_revenue(self) -> float:
        return Payment.objects.filter(status='success').aggregate(
            total=Sum('amount')
        )['total'] or 0.0

    def total_revenue_by_period(self, start_date, end_date) -> float:
        return Payment.objects.filter(
            status='success', paid_at__range=[start_date, end_date]
        ).aggregate(total=Sum('amount'))['total'] or 0.0


class PaymentReceiptRepository:
    def get_by_payment(self, payment_id: int) -> PaymentReceipt | None:
        return PaymentReceipt.objects.filter(payment_id=payment_id).first()

    def get_by_receipt_number(self, number: str) -> PaymentReceipt | None:
        return PaymentReceipt.objects.filter(receipt_number=number).first()

    def create_receipt(self, **kwargs) -> PaymentReceipt:
        return PaymentReceipt.objects.create(**kwargs)
