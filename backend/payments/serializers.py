# payments/serializers.py - CORRECTED VERSION
from rest_framework import serializers
from .models import Account, Transaction, Card
from decimal import Decimal
import uuid


class AccountSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Account
        fields = [
            'id', 'account_number', 'account_type', 'user', 
            'user_email', 'user_name', 'balance', 'currency',
            'is_active', 'created_at', 'available_balance', 'is_verified'
        ]
        read_only_fields = ['id', 'account_number', 'created_at']
    
    def get_user_name(self, obj):
        if obj.user.first_name and obj.user.last_name:
            return f"{obj.user.first_name} {obj.user.last_name}"
        return obj.user.email
    
    def validate_balance(self, value):
        if value < Decimal('0.00'):
            raise serializers.ValidationError("Balance cannot be negative.")
        return value


class AccountBalanceSerializer(serializers.ModelSerializer):
    """Serializer for account balance information"""
    user_name = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Account
        fields = [
            'id', 'account_number', 'balance', 'currency',
            'account_type', 'user_name', 'is_active', 'available_balance'
        ]
        read_only_fields = ['id', 'account_number', 'balance', 'currency', 'account_type', 'is_active', 'available_balance']
    
    def get_user_name(self, obj):
        if obj.user.first_name and obj.user.last_name:
            return f"{obj.user.first_name} {obj.user.last_name}"
        return obj.user.email


class TransactionSerializer(serializers.ModelSerializer):
    # ADDED: Alias fields for backward compatibility with tests
    from_account = serializers.PrimaryKeyRelatedField(
        queryset=Account.objects.all(),
        write_only=True,
        required=False,
        source='account'  # Map to the actual model field
    )
    
    to_account = serializers.PrimaryKeyRelatedField(
        queryset=Account.objects.all(),
        write_only=True,
        required=False,
        source='recipient_account'  # Map to the actual model field
    )
    
    # Existing computed fields
    account_info = serializers.SerializerMethodField()
    recipient_account_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_id', 'transaction_type', 'amount',
            'currency', 'description', 'status', 'created_at',
            'account', 'recipient_account',  # Actual model fields
            'from_account', 'to_account',    # Alias fields for input
            'account_info', 'recipient_account_info',
            'recipient_name', 'metadata', 'completed_at'
        ]
        read_only_fields = ['transaction_id', 'created_at', 'id', 'completed_at']
    
    def get_account_info(self, obj):
        """Get info for the source account"""
        if obj.account:
            return {
                'id': obj.account.id,
                'account_number': obj.account.account_number,
                'user_email': obj.account.user.email,
                'user_name': f"{obj.account.user.first_name} {obj.account.user.last_name}",
                'account_type': obj.account.account_type
            }
        return None
    
    def get_recipient_account_info(self, obj):
        """Get info for the recipient account"""
        if obj.recipient_account:
            return {
                'id': obj.recipient_account.id,
                'account_number': obj.recipient_account.account_number,
                'user_email': obj.recipient_account.user.email,
                'user_name': f"{obj.recipient_account.user.first_name} {obj.recipient_account.user.last_name}",
                'account_type': obj.recipient_account.account_type
            }
        return None
    
    def validate_amount(self, value):
        if value <= Decimal('0.00'):
            raise serializers.ValidationError("Amount must be greater than 0.")
        return value


class QuickTransferSerializer(serializers.Serializer):
    """Serializer for quick transfer"""
    to_account_number = serializers.CharField(max_length=20, min_length=1)
    amount = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        min_value=Decimal('0.01')
    )
    description = serializers.CharField(
        required=False, 
        allow_blank=True, 
        default="", 
        max_length=255
    )
    
    def validate_to_account_number(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError("Account number is required.")
        return value.strip()
    
    def validate_amount(self, value):
        if value <= Decimal('0.00'):
            raise serializers.ValidationError("Amount must be greater than 0.")
        return value
    
    def validate(self, data):
        # Additional validation can be added here
        return data


class CardSerializer(serializers.ModelSerializer):
    account_number = serializers.CharField(source='account.account_number', read_only=True)
    
    class Meta:
        model = Card
        fields = [
            'id', 'card_type', 'last_four', 
            'card_holder_name', 'status', 'created_at',
            'account', 'account_number', 'card_network',
            'expiry_month', 'expiry_year', 'is_default'
        ]
        read_only_fields = ['id', 'last_four', 'created_at']
    
    def validate_last_four(self, value):
        if len(value) != 4:
            raise serializers.ValidationError("Last four digits must be exactly 4 characters.")
        if not value.isdigit():
            raise serializers.ValidationError("Last four digits must be numeric.")
        return value


# Additional serializers for specific operations
class DepositWithdrawalSerializer(serializers.Serializer):
    """Serializer for deposit and withdrawal operations"""
    amount = serializers.DecimalField(  # Removed account_id - it's in the URL
        max_digits=12, 
        decimal_places=2, 
        min_value=Decimal('0.01')
    )
    description = serializers.CharField(
        required=False, 
        allow_blank=True, 
        default="", 
        max_length=255
    )
    
    def validate_amount(self, value):
        if value <= Decimal('0.00'):
            raise serializers.ValidationError("Amount must be greater than 0.")
        return value


class TransactionStatusSerializer(serializers.Serializer):
    """Serializer for updating transaction status"""
    status = serializers.ChoiceField(
        choices=['pending', 'completed', 'failed', 'cancelled']
    )
    notes = serializers.CharField(required=False, allow_blank=True, max_length=500)