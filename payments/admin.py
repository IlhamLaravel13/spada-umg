from django.contrib import admin
from .models import Payment, PaymentReceipt


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'invoice_number', 'user', 'payment_type', 'amount', 'status',
        'payment_method', 'paid_at', 'created_at'
    ]
    list_filter = ['status', 'payment_type', 'payment_method', 'created_at']
    search_fields = [
        'invoice_number', 'transaction_id', 'user__username',
        'user__email', 'user__nim', 'description'
    ]
    list_editable = ['status']
    list_per_page = 25
    date_hierarchy = 'created_at'
    readonly_fields = ['invoice_number', 'transaction_id', 'created_at', 'updated_at']

    fieldsets = (
        (None, {'fields': ('user', 'payment_type', 'amount', 'status')}),
        ('Payment Info', {
            'fields': (
                'payment_method', 'invoice_number', 'description',
                'transaction_id', 'payment_url'
            )
        }),
        ('Timeline', {
            'fields': ('paid_at', 'expired_at', 'created_at', 'updated_at')
        }),
        ('Metadata', {'fields': ('metadata',)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(PaymentReceipt)
class PaymentReceiptAdmin(admin.ModelAdmin):
    list_display = ['receipt_number', 'payment', 'created_at']
    search_fields = ['receipt_number', 'payment__invoice_number', 'notes']
    readonly_fields = ['created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('payment')
