from rest_framework import serializers
from .models import Account, Transaction, Card, PaymentMethod
from decimal import Decimal


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'
        read_only_fields = ('account_number', 'created_at', 'updated_at')


class SecureCardSerializer(serializers.ModelSerializer):
    """Serializer that never exposes sensitive data"""
    class Meta:
        model = Card
        fields = ['id', 'last_four', 'card_type', 'cardholder_name', 
                 'expiry_month', 'expiry_year', 'status', 'brand', 'created_at']
        read_only_fields = ['last_four', 'created_at']


class TransactionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['account', 'transaction_type', 'amount', 'currency',
                  'recipient_account', 'recipient_name', 'description']
    
    def validate(self, data):
        # Validate recipient account exists
        if data.get('recipient_account'):
            if not data['recipient_account'].is_active:
                raise serializers.ValidationError("Recipient account is not active")
        
        # Validate amount against account balance
        account = data['account']
        if data['amount'] > account.available_balance:
            raise serializers.ValidationError("Insufficient balance")
        
        return data


class TransactionSerializer(serializers.ModelSerializer):
    """Main transaction serializer - ADD THIS if missing"""
    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ('transaction_id', 'created_at', 'completed_at')


class CardSerializer(serializers.ModelSerializer):
    """Regular card serializer - ADD THIS if missing"""
    class Meta:
        model = Card
        fields = ['id', 'last_four', 'card_type', 'cardholder_name', 
                 'expiry_month', 'expiry_year', 'status', 'brand', 'created_at',
                 'spending_limit', 'token_expires_at']
        read_only_fields = ['last_four', 'created_at', 'card_token']


class TransferRequestSerializer(serializers.Serializer):
    recipient_account_number = serializers.CharField(max_length=20)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=Decimal('0.01'))
    currency = serializers.CharField(max_length=3, default='USD')
    description = serializers.CharField(required=False, allow_blank=True, max_length=500)
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value


class AccountBalanceSerializer(serializers.Serializer):
    """Serializer for account balance endpoint - ADD THIS if missing"""
    balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    available_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    currency = serializers.CharField(max_length=3)
    pending_transactions = serializers.IntegerField()
    total_savings = serializers.DecimalField(max_digits=15, decimal_places=2)


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ['id', 'method_type', 'is_default', 'created_at', 'last_used_at']
        read_only_fields = ['created_at', 'last_used_at']