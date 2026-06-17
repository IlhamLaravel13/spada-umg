from django.db.models import QuerySet, Q
from .models import Certificate, CertificateTemplate


class CertificateTemplateRepository:
    def get_active(self) -> QuerySet[CertificateTemplate]:
        return CertificateTemplate.objects.filter(is_active=True)

    def get_by_id(self, template_id: int) -> CertificateTemplate | None:
        return CertificateTemplate.objects.filter(id=template_id).first()

    def get_by_orientation(self, orientation: str) -> QuerySet[CertificateTemplate]:
        return CertificateTemplate.objects.filter(
            is_active=True, orientation=orientation
        )

    def create_template(self, **kwargs) -> CertificateTemplate:
        return CertificateTemplate.objects.create(**kwargs)


class CertificateRepository:
    def get_by_id(self, certificate_id: int) -> Certificate | None:
        return Certificate.objects.select_related(
            'user', 'template'
        ).filter(id=certificate_id).first()

    def get_by_number(self, number: str) -> Certificate | None:
        return Certificate.objects.select_related(
            'user', 'template'
        ).filter(certificate_number=number).first()

    def get_user_certificates(self, user_id: int) -> QuerySet[Certificate]:
        return Certificate.objects.filter(user_id=user_id)

    def get_by_type(self, certificate_type: str) -> QuerySet[Certificate]:
        return Certificate.objects.filter(certificate_type=certificate_type)

    def get_verified(self) -> QuerySet[Certificate]:
        return Certificate.objects.filter(is_verified=True)

    def search(self, query: str) -> QuerySet[Certificate]:
        return Certificate.objects.filter(
            Q(certificate_number__icontains=query) |
            Q(title__icontains=query) |
            Q(user__username__icontains=query) |
            Q(user__email__icontains=query) |
            Q(user__nim__icontains=query) |
            Q(description__icontains=query)
        )

    def create_certificate(self, **kwargs) -> Certificate:
        return Certificate.objects.create(**kwargs)

    def update_certificate(self, cert_id: int, **kwargs) -> Certificate | None:
        updated = Certificate.objects.filter(id=cert_id).update(**kwargs)
        if updated:
            return self.get_by_id(cert_id)
        return None

    def verify_certificate(self, cert_id: int) -> Certificate | None:
        return self.update_certificate(cert_id, is_verified=True)

    def count_by_type(self) -> dict:
        return {
            ctype: Certificate.objects.filter(certificate_type=ctype).count()
            for ctype, _ in Certificate.TYPE_CHOICES
        }

    def get_recent(self, limit: int = 10) -> QuerySet[Certificate]:
        return Certificate.objects.select_related('user').order_by('-issued_date')[:limit]

    def get_expiring_soon(self, days: int = 30) -> QuerySet[Certificate]:
        from django.utils import timezone
        from datetime import timedelta
        cutoff = timezone.now().date() + timedelta(days=days)
        return Certificate.objects.filter(
            expiry_date__lte=cutoff, expiry_date__gte=timezone.now().date()
        )
