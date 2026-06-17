from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta
from .models import Certificate, CertificateTemplate
from .services import CertificateService
from .repositories import CertificateRepository

User = get_user_model()


class CertificateModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='mahasiswa1', password='test1234',
            email='mhs@umg.ac.id', nim='2024001', role='mahasiswa'
        )

    def test_create_certificate(self):
        cert = Certificate.objects.create(
            user=self.user,
            certificate_type='course',
            title='Sertifikat Course Python',
            certificate_number=CertificateService.generate_certificate_number('course'),
            issued_date=date.today(),
        )
        self.assertEqual(cert.certificate_type, 'course')
        self.assertFalse(cert.is_verified)
        self.assertEqual(str(cert), f"{cert.certificate_number} - {cert.user}")

    def test_certificate_expiry(self):
        cert = Certificate.objects.create(
            user=self.user,
            certificate_type='completion',
            title='Test Expired',
            certificate_number='TST-001',
            issued_date=date.today() - timedelta(days=365),
            expiry_date=date.today() - timedelta(days=1),
        )
        self.assertTrue(cert.expiry_date < timezone.now().date())


class CertificateServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='mahasiswa2', password='test1234',
            email='mhs2@umg.ac.id', nim='2024002', role='mahasiswa'
        )

    def test_create_certificate_service(self):
        svc = CertificateService()
        result = svc.create_certificate(
            user=self.user,
            cert_type='course',
            title='Python Programming',
            description='Sertifikat kelulusan kursus Python',
        )
        self.assertTrue(result['success'])
        self.assertEqual(result['certificate'].title, 'Python Programming')

    def test_generate_certificate_number(self):
        number = CertificateService.generate_certificate_number('course')
        self.assertTrue(number.startswith('CRS/'))

        number2 = CertificateService.generate_certificate_number('achievement')
        self.assertTrue(number2.startswith('ACH/'))

    def test_verify_certificate_not_found(self):
        svc = CertificateService()
        result = svc.verify_certificate('NONEXISTENT')
        self.assertFalse(result['success'])
        self.assertIn('tidak ditemukan', result['error'])

    def test_verify_valid_certificate(self):
        cert = Certificate.objects.create(
            user=self.user,
            certificate_type='course',
            title='Valid Cert',
            certificate_number='VALID-001',
            issued_date=date.today(),
            is_verified=True,
        )
        svc = CertificateService()
        result = svc.verify_certificate('VALID-001')
        self.assertTrue(result['success'])
        self.assertTrue(result['is_valid'])


class CertificateRepositoryTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='mahasiswa3', password='test1234',
            email='mhs3@umg.ac.id', nim='2024003', role='mahasiswa'
        )
        self.repo = CertificateRepository()
        self.cert = Certificate.objects.create(
            user=self.user,
            certificate_type='participation',
            title='Seminar AI',
            certificate_number='PRT-001',
            issued_date=date.today(),
        )

    def test_get_by_number(self):
        found = self.repo.get_by_number('PRT-001')
        self.assertIsNotNone(found)
        self.assertEqual(found.title, 'Seminar AI')

    def test_verify_certificate(self):
        result = self.repo.verify_certificate(self.cert.id)
        self.assertIsNotNone(result)
        self.assertTrue(result.is_verified)

    def test_get_user_certificates(self):
        Certificate.objects.create(
            user=self.user, certificate_type='course',
            title='Another Cert', certificate_number='CRS-001',
            issued_date=date.today(),
        )
        certs = self.repo.get_user_certificates(self.user.id)
        self.assertEqual(certs.count(), 2)
