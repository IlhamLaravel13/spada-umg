from django.contrib import admin
from .models import CertificateTemplate, Certificate


@admin.register(CertificateTemplate)
class CertificateTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'orientation', 'is_active', 'created_at']
    list_filter = ['orientation', 'is_active']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    fieldsets = (
        (None, {'fields': ('name', 'description')}),
        ('Template Files', {'fields': ('template_file', 'background_image')}),
        ('Settings', {'fields': ('orientation', 'is_active')}),
    )


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = [
        'certificate_number', 'user', 'title', 'certificate_type',
        'is_verified', 'issued_date', 'expiry_date', 'created_at'
    ]
    list_filter = ['certificate_type', 'is_verified', 'issued_date']
    search_fields = [
        'certificate_number', 'title', 'user__username',
        'user__email', 'user__nim', 'description'
    ]
    list_editable = ['is_verified']
    date_hierarchy = 'issued_date'
    readonly_fields = ['certificate_number', 'created_at']

    fieldsets = (
        (None, {'fields': ('user', 'certificate_type', 'title', 'description')}),
        ('Certificate Info', {
            'fields': (
                'certificate_number', 'template', 'is_verified',
                'verification_url'
            )
        }),
        ('Files', {'fields': ('pdf_file', 'qr_code')}),
        ('Dates', {'fields': ('issued_date', 'expiry_date', 'created_at')}),
        ('Metadata', {'fields': ('metadata',)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'template')
