from rest_framework import serializers
from .models import Certificate, CertificateTemplate


class CertificateTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CertificateTemplate
        fields = [
            'id', 'name', 'description', 'template_file',
            'background_image', 'orientation', 'is_active', 'created_at',
        ]


class CertificateSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    type_display = serializers.SerializerMethodField()
    template_name = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = Certificate
        fields = [
            'id', 'user', 'user_name', 'certificate_type', 'type_display',
            'title', 'description', 'certificate_number', 'template',
            'template_name', 'pdf_file', 'qr_code', 'verification_url',
            'issued_date', 'expiry_date', 'is_expired', 'is_verified',
            'created_at',
        ]
        read_only_fields = [
            'id', 'certificate_number', 'pdf_file', 'qr_code',
            'verification_url', 'is_verified', 'created_at',
        ]

    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def get_type_display(self, obj):
        return obj.get_certificate_type_display()

    def get_template_name(self, obj):
        return obj.template.name if obj.template else None

    def get_is_expired(self, obj):
        from django.utils import timezone
        if obj.expiry_date:
            return obj.expiry_date < timezone.now().date()
        return False


class CertificateCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = [
            'user', 'certificate_type', 'title', 'description',
            'template', 'issued_date', 'expiry_date', 'metadata',
        ]


class CertificateVerifySerializer(serializers.Serializer):
    certificate_number = serializers.CharField(max_length=100)

    def validate_certificate_number(self, value):
        if not Certificate.objects.filter(certificate_number=value).exists():
            raise serializers.ValidationError('Sertifikat tidak ditemukan.')
        return value
