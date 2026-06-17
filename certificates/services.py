import io
import uuid
import logging
from datetime import date

from django.conf import settings
from django.urls import reverse
from django.db import transaction
from django.core.files.base import ContentFile
from django.utils import timezone

from .models import Certificate, CertificateTemplate
from .repositories import CertificateRepository, CertificateTemplateRepository

logger = logging.getLogger(__name__)


class CertificateService:
    def __init__(self):
        self.repo = CertificateRepository()
        self.template_repo = CertificateTemplateRepository()

    @staticmethod
    def generate_certificate_number(cert_type: str = 'course') -> str:
        prefix = {
            'completion': 'CPL',
            'achievement': 'ACH',
            'participation': 'PRT',
            'course': 'CRS',
            'academic': 'ACM',
        }.get(cert_type, 'CERT')
        date_part = date.today().strftime('%Y%m%d')
        unique_part = uuid.uuid4().hex[:10].upper()
        return f"{prefix}/{date_part}/{unique_part}"

    def create_certificate(self, user, cert_type: str, title: str,
                           description: str = '', template_id: int = None,
                           issued_date: date = None, expiry_date: date = None,
                           metadata: dict = None, **extra) -> dict:
        try:
            with transaction.atomic():
                cert_number = self.generate_certificate_number(cert_type)
                template = None
                if template_id:
                    template = self.template_repo.get_by_id(template_id)

                if not issued_date:
                    issued_date = date.today()

                cert = self.repo.create_certificate(
                    user=user,
                    certificate_type=cert_type,
                    title=title,
                    description=description,
                    certificate_number=cert_number,
                    template=template,
                    issued_date=issued_date,
                    expiry_date=expiry_date,
                    metadata=metadata or {},
                    **extra,
                )

                self._generate_pdf(cert)
                self._generate_qr_code(cert)
                self._set_verification_url(cert)

                return {'success': True, 'certificate': cert}
        except Exception as e:
            logger.error(f'Create certificate error: {e}')
            return {'success': False, 'error': str(e)}

    def _generate_pdf(self, certificate: Certificate) -> None:
        try:
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib.units import mm
            from reportlab.pdfgen import canvas
            from reportlab.lib.colors import HexColor

            buffer = io.BytesIO()

            if certificate.template and certificate.template.orientation == 'landscape':
                width, height = landscape(A4)
            else:
                width, height = A4

            c = canvas.Canvas(buffer, pagesize=(width, height))

            if certificate.template and certificate.template.background_image:
                try:
                    bg_path = certificate.template.background_image.path
                    c.drawImage(bg_path, 0, 0, width=width, height=height,
                                preserveAspectRatio=True, anchor='c')
                except Exception:
                    pass

            c.setFillColor(HexColor('#1a365d'))
            c.setFont('Helvetica-Bold', 28)
            c.drawCentredString(width / 2, height * 0.75, certificate.title)

            c.setFillColor(HexColor('#2d3748'))
            c.setFont('Helvetica', 14)
            c.drawCentredString(width / 2, height * 0.65, 'Diberikan kepada')

            c.setFillColor(HexColor('#1a365d'))
            c.setFont('Helvetica-Bold', 22)
            user_name = certificate.user.get_full_name() or certificate.user.username
            c.drawCentredString(width / 2, height * 0.58, user_name)

            c.setFillColor(HexColor('#4a5568'))
            c.setFont('Helvetica', 12)
            text = certificate.description or f'Sertifikat {certificate.get_certificate_type_display()}'
            c.drawCentredString(width / 2, height * 0.50, text)

            c.setFont('Helvetica', 10)
            c.drawCentredString(
                width / 2, height * 0.40,
                f'Nomor: {certificate.certificate_number}'
            )
            c.drawCentredString(
                width / 2, height * 0.36,
                f'Tanggal: {certificate.issued_date.strftime("%d %B %Y")}'
            )

            c.setStrokeColor(HexColor('#2b6cb0'))
            c.setLineWidth(2)
            c.rect(20, 20, width - 40, height - 40)

            c.showPage()
            c.save()

            buffer.seek(0)
            filename = f'certificate_{certificate.certificate_number}.pdf'
            certificate.pdf_file.save(filename, ContentFile(buffer.read()), save=True)
            buffer.close()
        except ImportError:
            logger.warning('reportlab not installed, skipping PDF generation')
        except Exception as e:
            logger.error(f'PDF generation error: {e}')

    def _generate_qr_code(self, certificate: Certificate) -> None:
        try:
            import qrcode
            from PIL import Image

            verification_url = certificate.verification_url or self._build_verification_url(certificate)

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(verification_url)
            qr.make(fit=True)

            img = qr.make_image(fill_color='#1a365d', back_color='white')

            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)

            filename = f'qr_{certificate.certificate_number}.png'
            certificate.qr_code.save(filename, ContentFile(buffer.read()), save=True)
            buffer.close()
        except ImportError:
            logger.warning('qrcode not installed, skipping QR generation')
        except Exception as e:
            logger.error(f'QR generation error: {e}')

    def _build_verification_url(self, certificate: Certificate) -> str:
        base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
        path = reverse('certificates:verify')
        return f"{base_url}{path}?number={certificate.certificate_number}"

    def _set_verification_url(self, certificate: Certificate) -> None:
        url = self._build_verification_url(certificate)
        Certificate.objects.filter(id=certificate.id).update(verification_url=url)

    def verify_certificate(self, certificate_number: str) -> dict:
        certificate = self.repo.get_by_number(certificate_number)
        if not certificate:
            return {'success': False, 'error': 'Sertifikat tidak ditemukan.'}

        is_valid = True
        reasons = []

        if certificate.expiry_date and certificate.expiry_date < timezone.now().date():
            is_valid = False
            reasons.append('Sertifikat sudah kadaluwarsa.')

        if not certificate.is_verified:
            is_valid = False
            reasons.append('Sertifikat belum diverifikasi.')

        return {
            'success': True,
            'is_valid': is_valid,
            'certificate': certificate,
            'reasons': reasons,
        }

    def get_user_certificates(self, user_id: int, cert_type: str = None):
        qs = self.repo.get_user_certificates(user_id)
        if cert_type:
            qs = qs.filter(certificate_type=cert_type)
        return qs

    def get_dashboard_data(self) -> dict:
        return {
            'by_type': self.repo.count_by_type(),
            'recent': self.repo.get_recent(10),
            'total': Certificate.objects.count(),
            'verified': Certificate.objects.filter(is_verified=True).count(),
        }
