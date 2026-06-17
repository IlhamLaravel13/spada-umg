from rest_framework import serializers
from .models import Payment, PaymentReceipt


class PaymentSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    type_display = serializers.SerializerMethodField()
    method_display = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'user_name', 'payment_type', 'type_display',
            'amount', 'status', 'status_display', 'payment_method',
            'method_display', 'invoice_number', 'description',
            'transaction_id', 'payment_url', 'paid_at', 'expired_at',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'invoice_number', 'transaction_id', 'payment_url',
            'paid_at', 'created_at', 'updated_at',
        ]

    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def get_status_display(self, obj):
        return obj.get_status_display()

    def get_type_display(self, obj):
        return obj.get_payment_type_display()

    def get_method_display(self, obj):
        return obj.get_payment_method_display() if obj.payment_method else ''


class PaymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'payment_type', 'amount', 'description', 'payment_method',
        ]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Jumlah pembayaran harus lebih dari 0.')
        return value


class PaymentConfirmSerializer(serializers.Serializer):
    transaction_id = serializers.CharField(max_length=200)
    status = serializers.ChoiceField(choices=['success', 'failed'])
    payment_method = serializers.CharField(max_length=20, required=False)


class PaymentReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentReceipt
        fields = ['id', 'payment', 'receipt_file', 'receipt_number', 'notes', 'created_at']
        read_only_fields = ['id', 'receipt_number', 'created_at']


class PaymentStatusSerializer(serializers.Serializer):
    invoice_number = serializers.CharField(max_length=50)
    status = serializers.CharField()
    paid_at = serializers.DateTimeField(required=False)
    payment_method = serializers.CharField(required=False)
