from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Payment, PaymentReceipt
from .services import InvoiceService, PaymentService
from .repositories import PaymentRepository

User = get_user_model()


class PaymentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='mahasiswa1', password='test1234',
            email='mhs@umg.ac.id', nim='2024001', role='mahasiswa'
        )

    def test_create_payment(self):
        payment = Payment.objects.create(
            user=self.user,
            payment_type='ukt',
            amount=5000000,
            invoice_number=InvoiceService.generate_invoice_number('ukt'),
        )
        self.assertEqual(payment.status, 'pending')
        self.assertEqual(str(payment), f"{payment.invoice_number} - {payment.user}")

    def test_payment_status_choices(self):
        payment = Payment.objects.create(
            user=self.user,
            payment_type='spp',
            amount=2500000,
            invoice_number=InvoiceService.generate_invoice_number('spp'),
        )
        for status, _ in Payment.STATUS_CHOICES:
            payment.status = status
            payment.save()
            self.assertEqual(payment.status, status)


class PaymentServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='mahasiswa2', password='test1234',
            email='mhs2@umg.ac.id', nim='2024002', role='mahasiswa'
        )

    def test_create_payment_service(self):
        svc = PaymentService()
        result = svc.create_payment(
            user=self.user,
            payment_type='semester',
            amount=3000000,
            description='Pembayaran Semester Genap 2024',
        )
        self.assertTrue(result['success'])
        self.assertEqual(result['payment'].payment_type, 'semester')

    def test_get_user_payments(self):
        Payment.objects.create(
            user=self.user, payment_type='ukt', amount=5000000,
            invoice_number='INV-001', status='success', paid_at=timezone.now(),
        )
        Payment.objects.create(
            user=self.user, payment_type='spp', amount=2500000,
            invoice_number='INV-002', status='pending',
        )
        svc = PaymentService()
        payments = svc.get_user_payments(self.user.id)
        self.assertEqual(payments.count(), 2)

        pending = svc.get_user_payments(self.user.id, status='pending')
        self.assertEqual(pending.count(), 1)


class PaymentRepositoryTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='mahasiswa3', password='test1234',
            email='mhs3@umg.ac.id', nim='2024003', role='mahasiswa'
        )
        self.repo = PaymentRepository()
        self.payment = Payment.objects.create(
            user=self.user, payment_type='registrasi', amount=1000000,
            invoice_number='REG-001',
        )

    def test_get_by_invoice(self):
        found = self.repo.get_by_invoice('REG-001')
        self.assertIsNotNone(found)
        self.assertEqual(found.amount, 1000000)

    def test_mark_success(self):
        result = self.repo.mark_success(self.payment.id)
        self.assertIsNotNone(result)
        self.assertEqual(result.status, 'success')
        self.assertIsNotNone(result.paid_at)


class InvoiceServiceTest(TestCase):
    def test_generate_invoice_number(self):
        inv = InvoiceService.generate_invoice_number('ukt')
        self.assertTrue(inv.startswith('UKT/'))

        inv2 = InvoiceService.generate_invoice_number('spp')
        self.assertTrue(inv2.startswith('SPP/'))

    def test_generate_receipt_number(self):
        rec = InvoiceService.generate_receipt_number()
        self.assertTrue(rec.startswith('REC/'))
