"""
payments/serializers.py - Serializers for Payment API
"""
from rest_framework import serializers
from .models import Payment, PaymentCode
from django.contrib.auth import get_user_model
from accounts.models import Account

User = get_user_model()


class PaymentCodeSerializer(serializers.ModelSerializer):
    """Serializer for PaymentCode"""
    account_number = serializers.CharField(source='account.account_number', read_only=True)
    account_email = serializers.EmailField(source='account.email', read_only=True)
    
    class Meta:
        model = PaymentCode
        fields = [
            'id', 'code', 'account', 'account_number', 'account_email',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment"""
    account_number = serializers.CharField(source='account.account_number', read_only=True)
    account_email = serializers.EmailField(source='account.email', read_only=True)
    account_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Payment
        fields = [
            'id', 'reference', 'account', 'account_number', 'account_email',
            'account_name', 'payment_code', 'amount', 'sender', 'description',
            'status', 'balance_before', 'balance_after', 'metadata', 
            'created_at', 'processed_at'
        ]
        read_only_fields = [
            'reference', 'balance_before', 'balance_after', 
            'metadata', 'created_at', 'processed_at'
        ]
    
    def get_account_name(self, obj):
        """Get account holder's full name"""
        if obj.account:
            return f"{obj.account.first_name} {obj.account.last_name}".strip()
        return ""


class ProcessPaymentSerializer(serializers.Serializer):
    """Serializer for processing payments"""
    payment_code = serializers.CharField(max_length=50, required=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    sender = serializers.CharField(max_length=255, required=True)
    description = serializers.CharField(required=False, allow_blank=True)
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive")
        return value


class AssignPaymentCodeSerializer(serializers.Serializer):
    """Serializer for assigning payment codes"""
    account_number = serializers.CharField(max_length=50, required=True)
    code = serializers.CharField(max_length=50, required=True)