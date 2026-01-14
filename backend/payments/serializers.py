# payments/serializers.py - UPDATED WITH WALLET SYSTEM
from rest_framework import serializers
from .models import (
    Account, Transaction, Card, PaymentMethod, AuditLog,
    MainBusinessWallet, EmployeePlatformWallet, 
    PaymentTransactionNotification, WithdrawalRequest, ActivityFeed,
    ManualPaymentRelease, KYCVerification  # NEW: Added manual compliance models
)
from decimal import Decimal
import uuid
from django.utils import timezone


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


# ============================================
# WALLET SYSTEM SERIALIZERS
# ============================================

class MainBusinessWalletSerializer(serializers.ModelSerializer):
    """Serializer for main business wallet"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = MainBusinessWallet
        fields = [
            'id', 'wallet_number', 'wallet_type', 'user', 'user_email', 'user_name',
            'total_balance', 'available_balance', 'currency', 'display_name',
            'connected_bank_name', 'connected_bank_account', 'connected_bank_routing',
            'is_active', 'auto_replenish', 'min_balance_threshold',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'wallet_number', 'created_at', 'updated_at']
    
    def get_user_name(self, obj):
        if obj.user.first_name and obj.user.last_name:
            return f"{obj.user.first_name} {obj.user.last_name}"
        return obj.user.email


class EmployeePlatformWalletSerializer(serializers.ModelSerializer):
    """Serializer for employee platform wallet"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField(read_only=True)
    preferred_bank_info = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = EmployeePlatformWallet
        fields = [
            'id', 'wallet_number', 'user', 'user_email', 'user_name', 'display_name',
            'platform_balance', 'available_for_withdrawal', 'pending_withdrawal', 'currency',
            'preferred_bank', 'preferred_bank_info', 'auto_withdraw_enabled', 'withdraw_threshold',
            'status', 'last_withdrawal_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'wallet_number', 'created_at', 'updated_at']
    
    def get_user_name(self, obj):
        if obj.user.first_name and obj.user.last_name:
            return f"{obj.user.first_name} {obj.user.last_name}"
        return obj.user.email
    
    def get_preferred_bank_info(self, obj):
        if obj.preferred_bank:
            return {
                'id': obj.preferred_bank.id,
                'account_number': obj.preferred_bank.account_number,
                'account_type': obj.preferred_bank.account_type
            }
        return None


class PaymentTransactionNotificationSerializer(serializers.ModelSerializer):
    """Serializer for payment notifications"""
    sender_email = serializers.EmailField(source='sender.email', read_only=True)
    sender_name = serializers.SerializerMethodField(read_only=True)
    receiver_email = serializers.EmailField(source='receiver.email', read_only=True)
    receiver_name = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = PaymentTransactionNotification
        fields = [
            'id', 'reference_code', 'transaction', 'notification_type',
            'sender', 'sender_email', 'sender_name',
            'receiver', 'receiver_email', 'receiver_name',
            'amount', 'currency', 'full_message', 'short_message', 'emoji',
            'sender_account', 'receiver_account', 'bank_routing',
            'email_sent', 'push_sent', 'website_delivered',
            'created_at', 'delivered_at'
        ]
        read_only_fields = ['id', 'reference_code', 'created_at', 'delivered_at']
    
    def get_sender_name(self, obj):
        if obj.sender.first_name and obj.sender.last_name:
            return f"{obj.sender.first_name} {obj.sender.last_name}"
        return obj.sender.email
    
    def get_receiver_name(self, obj):
        if obj.receiver.first_name and obj.receiver.last_name:
            return f"{obj.receiver.first_name} {obj.receiver.last_name}"
        return obj.receiver.email


class WithdrawalRequestSerializer(serializers.ModelSerializer):
    """Serializer for withdrawal requests"""
    employee_wallet_info = serializers.SerializerMethodField(read_only=True)
    bank_account_info = serializers.SerializerMethodField(read_only=True)
    assigned_agent_info = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = WithdrawalRequest
        fields = [
            'id', 'withdrawal_reference', 'employee_wallet', 'employee_wallet_info',
            'amount', 'currency', 'bank_account', 'bank_account_info',
            'status', 'compliance_form_filled', 'agent_call_scheduled', 'agent_call_completed',
            'tac_code', 'tac_generated_at', 'tac_verified_at',
            'assigned_agent', 'assigned_agent_info', 'agent_call_date', 'agent_call_duration', 'agent_notes',
            'processed_at', 'transaction_reference',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'withdrawal_reference', 'created_at', 'updated_at']
    
    def get_employee_wallet_info(self, obj):
        if obj.employee_wallet:
            return {
                'wallet_number': obj.employee_wallet.wallet_number,
                'user_email': obj.employee_wallet.user.email,
                'user_name': f"{obj.employee_wallet.user.first_name} {obj.employee_wallet.user.last_name}"
            }
        return None
    
    def get_bank_account_info(self, obj):
        if obj.bank_account:
            return {
                'id': obj.bank_account.id,
                'account_number': obj.bank_account.account_number,
                'account_type': obj.bank_account.account_type
            }
        return None
    
    def get_assigned_agent_info(self, obj):
        if obj.assigned_agent:
            return {
                'id': obj.assigned_agent.id,
                'email': obj.assigned_agent.email,
                'name': f"{obj.assigned_agent.first_name} {obj.assigned_agent.last_name}"
            }
        return None


class ActivityFeedSerializer(serializers.ModelSerializer):
    """Serializer for activity feed"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = ActivityFeed
        fields = [
            'id', 'user', 'user_email', 'user_name',
            'activity_type', 'reference', 'amount', 'currency',
            'display_text', 'emoji', 'color_class',
            'metadata', 'created_at', 'expires_at'
        ]
        read_only_fields = ['id', 'created_at', 'expires_at']
    
    def get_user_name(self, obj):
        if obj.user.first_name and obj.user.last_name:
            return f"{obj.user.first_name} {obj.user.last_name}"
        return obj.user.email


# ============================================
# WALLET OPERATION SERIALIZERS
# ============================================

class EmployerPaymentSerializer(serializers.Serializer):
    """Serializer for employer to pay employee"""
    employee_email = serializers.EmailField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=Decimal('0.01'))
    description = serializers.CharField(required=False, allow_blank=True, default="Payment from employer")
    sender_display_name = serializers.CharField(required=False, default="ecoveraLTD")
    
    def validate_amount(self, value):
        if value <= Decimal('0.00'):
            raise serializers.ValidationError("Amount must be greater than 0.")
        return value


class WithdrawalRequestCreateSerializer(serializers.Serializer):
    """Serializer for creating withdrawal request"""
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=Decimal('0.01'))
    bank_account_id = serializers.IntegerField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    
    def validate_amount(self, value):
        if value <= Decimal('0.00'):
            raise serializers.ValidationError("Amount must be greater than 0.")
        return value


class TACVerificationSerializer(serializers.Serializer):
    """Serializer for TAC verification"""
    tac_code = serializers.CharField(max_length=10, min_length=6)
    withdrawal_request_id = serializers.IntegerField()


class AgentCallScheduleSerializer(serializers.Serializer):
    """Serializer for scheduling agent call"""
    withdrawal_request_id = serializers.IntegerField()
    call_date = serializers.DateTimeField()
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class ComplianceFormSerializer(serializers.Serializer):
    """Serializer for compliance form"""
    withdrawal_request_id = serializers.IntegerField()
    answers = serializers.JSONField()  # Store form answers as JSON
    documents = serializers.ListField(
        child=serializers.IntegerField(),  # List of document IDs
        required=False
    )


# ============================================
# COMPLIANCE SERIALIZERS - UPDATED
# ============================================

class ManualPaymentRequestSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=Decimal('0.01'))
    currency = serializers.CharField(max_length=3, default='USD')
    description = serializers.CharField(required=False, allow_blank=True, default="")


class TACVerificationSerializer(serializers.Serializer):
    # UPDATED: Use compliance_id instead of reference_code
    compliance_id = serializers.CharField(max_length=100)
    tac_code = serializers.CharField(max_length=10, min_length=6)


class KYCFormSubmitSerializer(serializers.Serializer):
    # UPDATED: Use compliance_id instead of reference_code
    compliance_id = serializers.CharField(max_length=100)
    form_data = serializers.JSONField()
    documents = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=[]
    )


class AdminReleasePaymentSerializer(serializers.Serializer):
    # UPDATED: Use compliance_id
    compliance_id = serializers.CharField(max_length=100)
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class ScheduleVideoCallSerializer(serializers.Serializer):
    # UPDATED: Use compliance_id
    compliance_id = serializers.CharField(max_length=100)
    call_datetime = serializers.DateTimeField()
    call_link = serializers.URLField()
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class CompleteVideoCallSerializer(serializers.Serializer):
    # UPDATED: Use compliance_id
    compliance_id = serializers.CharField(max_length=100)
    approved = serializers.BooleanField()
    admin_notes = serializers.CharField(required=False, allow_blank=True, default="")


class ComplianceRequestSerializer(serializers.Serializer):
    """Generic compliance request serializer"""
    compliance_id = serializers.CharField(max_length=100)
    action = serializers.ChoiceField(choices=['approve', 'reject', 'request_info'])
    notes = serializers.CharField(required=False, allow_blank=True, default="")