from django.db import models

class Payment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
        ('refunded', 'Refunded'),
    )
    METHOD_CHOICES = (
        ('midtrans', 'Midtrans'),
        ('xendit', 'Xendit'),
        ('transfer', 'Transfer Bank'),
        ('cash', 'Tunai'),
    )
    TYPE_CHOICES = (
        ('ukt', 'UKT'),
        ('spp', 'SPP'),
        ('semester', 'Semester'),
        ('registrasi', 'Registrasi'),
        ('other', 'Lainnya'),
    )
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='payments')
    payment_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES, blank=True)
    invoice_number = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    transaction_id = models.CharField(max_length=200, blank=True)
    payment_url = models.URLField(blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    expired_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.invoice_number} - {self.user}"

class PaymentReceipt(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='receipt')
    receipt_file = models.FileField(upload_to='receipts/')
    receipt_number = models.CharField(max_length=50, unique=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
