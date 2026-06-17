from django.db import models

class CertificateTemplate(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    template_file = models.FileField(upload_to='certificate_templates/')
    background_image = models.ImageField(upload_to='certificate_templates/bg/', blank=True)
    orientation = models.CharField(max_length=10, choices=[('landscape', 'Landscape'), ('portrait', 'Portrait')], default='landscape')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Certificate(models.Model):
    TYPE_CHOICES = (
        ('completion', 'Completion'),
        ('achievement', 'Achievement'),
        ('participation', 'Participation'),
        ('course', 'Course Completion'),
        ('academic', 'Academic'),
    )
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='certificates')
    certificate_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    certificate_number = models.CharField(max_length=100, unique=True)
    template = models.ForeignKey(CertificateTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    pdf_file = models.FileField(upload_to='certificates/', blank=True)
    qr_code = models.ImageField(upload_to='certificates/qrcodes/', blank=True)
    verification_url = models.URLField(blank=True)
    issued_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-issued_date']
    
    def __str__(self):
        return f"{self.certificate_number} - {self.user}"
