import uuid
import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.db import transaction

from .models import Payment
from .repositories import PaymentRepository, PaymentReceiptRepository

logger = logging.getLogger(__name__)


class InvoiceService:
    @staticmethod
    def generate_invoice_number(payment_type: str = 'other') -> str:
        prefix = {
            'ukt': 'UKT',
            'spp': 'SPP',
            'semester': 'SMT',
            'registrasi': 'REG',
            'other': 'INV',
        }.get(payment_type, 'INV')
        date_part = datetime.now().strftime('%Y%m%d')
        unique_part = uuid.uuid4().hex[:8].upper()
        return f"{prefix}/{date_part}/{unique_part}"

    @staticmethod
    def generate_receipt_number() -> str:
        date_part = datetime.now().strftime('%Y%m%d')
        unique_part = uuid.uuid4().hex[:10].upper()
        return f"REC/{date_part}/{unique_part}"


class MidtransService:
    def __init__(self):
        self.repo = PaymentRepository()
        self.is_production = getattr(settings, 'MIDTRANS_IS_PRODUCTION', False)
        self.server_key = getattr(settings, 'MIDTRANS_SERVER_KEY', '')
        self.client_key = getattr(settings, 'MIDTRANS_CLIENT_KEY', '')

    def _get_base_url(self):
        if self.is_production:
            return 'https://app.midtrans.com'
        return 'https://app.sandbox.midtrans.com'

    def create_transaction(self, payment: Payment) -> dict:
        try:
            import requests
            transaction_details = {
                'order_id': payment.invoice_number,
                'gross_amount': int(payment.amount),
            }
            user = payment.user
            customer_details = {
                'first_name': user.first_name or user.username,
                'email': user.email,
                'phone': user.phone or '',
            }
            payload = {
                'transaction_details': transaction_details,
                'customer_details': customer_details,
                'credit_card': {'secure': True},
            }
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': f'Basic {self._encode_auth()}',
            }
            url = f"{self._get_base_url()}/snap/v1/transactions"
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            result = response.json()

            token = result.get('token', '')
            redirect_url = result.get('redirect_url', '')

            self.repo.update_payment(payment.id, **{
                'transaction_id': result.get('transaction_id', ''),
                'payment_url': redirect_url,
                'status': 'processing',
            })
            return {
                'success': True,
                'token': token,
                'redirect_url': redirect_url,
            }
        except ImportError:
            logger.error('requests library not installed')
            return {'success': False, 'error': 'Payment gateway unavailable'}
        except requests.RequestException as e:
            logger.error(f'Midtrans request failed: {e}')
            self.repo.update_status(payment.id, 'failed')
            return {'success': False, 'error': str(e)}

    def handle_notification(self, notification_data: dict) -> dict:
        try:
            order_id = notification_data.get('order_id')
            transaction_status = notification_data.get('transaction_status')
            status_code = notification_data.get('status_code', '')
            gross_amount = notification_data.get('gross_amount', '')
            signature_key = notification_data.get('signature_key', '')

            if not self._verify_signature(order_id, status_code, gross_amount, signature_key):
                return {'success': False, 'error': 'Invalid signature'}

            payment = self.repo.get_by_invoice(order_id)
            if not payment:
                return {'success': False, 'error': 'Payment not found'}

            status_map = {
                'capture': 'success',
                'settlement': 'success',
                'pending': 'pending',
                'deny': 'failed',
                'cancel': 'failed',
                'expire': 'expired',
                'refund': 'refunded',
                'partial_refund': 'refunded',
            }
            new_status = status_map.get(transaction_status, 'pending')

            if new_status == 'success':
                self.repo.mark_success(
                    payment.id,
                    transaction_id=notification_data.get('transaction_id', ''),
                    payment_method='midtrans',
                )
            else:
                self.repo.update_status(payment.id, new_status)

            return {'success': True, 'status': new_status, 'payment': payment}
        except Exception as e:
            logger.error(f'Midtrans notification error: {e}')
            return {'success': False, 'error': str(e)}

    def _encode_auth(self) -> str:
        import base64
        auth_str = f"{self.server_key}:"
        return base64.b64encode(auth_str.encode()).decode()

    def _verify_signature(self, order_id, status_code, gross_amount, signature_key) -> bool:
        raw = f"{order_id}{status_code}{gross_amount}{self.server_key}"
        computed = hashlib.sha512(raw.encode()).hexdigest()
        return computed == signature_key


class XenditService:
    def __init__(self):
        self.repo = PaymentRepository()
        self.api_key = getattr(settings, 'XENDIT_API_KEY', '')
        self.webhook_token = getattr(settings, 'XENDIT_WEBHOOK_TOKEN', '')

    def _get_base_url(self):
        return 'https://api.xendit.co'

    def _get_headers(self):
        import base64
        auth = base64.b64encode(f"{self.api_key}:".encode()).decode()
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Basic {auth}',
        }

    def create_invoice(self, payment: Payment, success_url: str = '',
                       failure_url: str = '') -> dict:
        try:
            import requests
            external_id = payment.invoice_number
            payload = {
                'external_id': external_id,
                'amount': int(payment.amount),
                'description': payment.description or f'Pembayaran {payment.get_payment_type_display()}',
                'customer': {
                    'given_names': payment.user.first_name or payment.user.username,
                    'email': payment.user.email,
                    'mobile_number': payment.user.phone or '',
                },
                'customer_notification_preference': {
                    'invoice_paid': ['email', 'whatsapp'],
                },
                'success_redirect_url': success_url,
                'failure_redirect_url': failure_url,
                'currency': 'IDR',
            }
            url = f"{self._get_base_url()}/v2/invoices"
            response = requests.post(url, json=payload, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            result = response.json()

            invoice_url = result.get('invoice_url', '')
            self.repo.update_payment(payment.id, **{
                'transaction_id': result.get('id', ''),
                'payment_url': invoice_url,
                'status': 'processing',
            })
            return {
                'success': True,
                'invoice_url': invoice_url,
                'xendit_id': result.get('id', ''),
            }
        except ImportError:
            logger.error('requests library not installed')
            return {'success': False, 'error': 'Payment gateway unavailable'}
        except requests.RequestException as e:
            logger.error(f'Xendit request failed: {e}')
            self.repo.update_status(payment.id, 'failed')
            return {'success': False, 'error': str(e)}

    def handle_callback(self, callback_data: dict) -> dict:
        try:
            external_id = callback_data.get('external_id', '')
            status = callback_data.get('status', '')
            payment = self.repo.get_by_invoice(external_id)
            if not payment:
                return {'success': False, 'error': 'Payment not found'}

            status_map = {
                'PAID': 'success',
                'EXPIRED': 'expired',
                'FAILED': 'failed',
            }
            new_status = status_map.get(status, 'pending')

            if new_status == 'success':
                self.repo.mark_success(
                    payment.id,
                    transaction_id=callback_data.get('id', ''),
                    payment_method='xendit',
                )
            else:
                self.repo.update_status(payment.id, new_status)

            return {'success': True, 'status': new_status, 'payment': payment}
        except Exception as e:
            logger.error(f'Xendit callback error: {e}')
            return {'success': False, 'error': str(e)}

    def _verify_webhook(self, request_body: bytes, callback_token: str) -> bool:
        return callback_token == self.webhook_token


class PaymentService:
    def __init__(self):
        self.repo = PaymentRepository()
        self.receipt_repo = PaymentReceiptRepository()
        self.invoice_service = InvoiceService()

    def create_payment(self, user, payment_type: str, amount: Decimal,
                       description: str = '', payment_method: str = '',
                       **extra) -> dict:
        try:
            with transaction.atomic():
                invoice = self.invoice_service.generate_invoice_number(payment_type)
                expired_at = timezone.now() + timedelta(hours=24)

                payment = self.repo.create_payment(
                    user=user,
                    payment_type=payment_type,
                    amount=amount,
                    description=description,
                    payment_method=payment_method,
                    invoice_number=invoice,
                    expired_at=expired_at,
                    **extra,
                )

                if payment_method == 'midtrans':
                    midtrans = MidtransService()
                    result = midtrans.create_transaction(payment)
                    if not result['success']:
                        raise Exception(result.get('error', 'Midtrans transaction failed'))
                    return {'success': True, 'payment': payment, 'gateway': result}

                elif payment_method == 'xendit':
                    xendit = XenditService()
                    result = xendit.create_invoice(payment)
                    if not result['success']:
                        raise Exception(result.get('error', 'Xendit transaction failed'))
                    return {'success': True, 'payment': payment, 'gateway': result}

                return {'success': True, 'payment': payment}
        except Exception as e:
            logger.error(f'Create payment error: {e}')
            return {'success': False, 'error': str(e)}

    def get_user_payments(self, user_id: int, status: str = None):
        qs = self.repo.get_user_payments(user_id)
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_payment_detail(self, payment_id: int, user_id: int = None) -> Payment | None:
        payment = self.repo.get_by_id(payment_id)
        if payment and user_id and payment.user_id != user_id:
            return None
        return payment

    def process_callback(self, provider: str, data: dict) -> dict:
        if provider == 'midtrans':
            midtrans = MidtransService()
            return midtrans.handle_notification(data)
        elif provider == 'xendit':
            xendit = XenditService()
            return xendit.handle_callback(data)
        return {'success': False, 'error': 'Unknown provider'}

    def expire_pending_payments(self) -> int:
        expired = self.repo.get_pending_expired()
        count = expired.count()
        for payment in expired:
            self.repo.update_status(payment.id, 'expired')
        return count

    def get_payment_stats(self, user_id: int = None) -> dict:
        if user_id:
            payments = Payment.objects.filter(user_id=user_id)
        else:
            payments = Payment.objects.all()
        return {
            'total': payments.count(),
            'success': payments.filter(status='success').count(),
            'pending': payments.filter(status='pending').count(),
            'failed': payments.filter(status='failed').count(),
            'total_amount': sum(p.amount for p in payments.filter(status='success')),
        }

    def get_dashboard_data(self) -> dict:
        return {
            'by_status': self.repo.count_by_status(),
            'total_revenue': self.repo.total_revenue(),
            'recent': Payment.objects.select_related('user').order_by('-created_at')[:10],
        }
