from rest_framework import serializers
from .models import Recipient, Transfer, TransferLog, TACCode
from django.contrib.auth import get_user_model

User = get_user_model()

class RecipientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipient
        fields = [
            'id', 'user', 'recipient_type', 'name', 'country', 'logo',
            'account_number', 'account_holder', 'swift_code', 'iban',
            'routing_number', 'bank_name', 'wallet_address', 'network',
            'is_favorite', 'is_verified', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RecipientCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipient
        fields = [
            'recipient_type', 'name', 'country', 'logo',
            'account_number', 'account_holder', 'swift_code', 'iban',
            'routing_number', 'bank_name', 'wallet_address', 'network',
            'is_favorite'
        ]
    
    def validate(self, data):
        recipient_type = data.get('recipient_type')
        
        # Validate bank/fintech recipients
        if recipient_type in ['bank', 'fintech']:
            if not data.get('account_number'):
                raise serializers.ValidationError("Account number is required for bank/fintech transfers.")
            if not data.get('account_holder'):
                raise serializers.ValidationError("Account holder name is required.")
        
        # Validate crypto recipients
        if recipient_type == 'crypto':
            if not data.get('wallet_address'):
                raise serializers.ValidationError("Wallet address is required for crypto transfers.")
            if not data.get('network'):
                raise serializers.ValidationError("Network is required for crypto transfers.")
        
        return data


class TransferLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransferLog
        fields = ['id', 'status', 'message', 'created_at']


class TransferSerializer(serializers.ModelSerializer):
    recipient_details = RecipientSerializer(source='recipient', read_only=True)
    sender_email = serializers.CharField(source='sender.email', read_only=True)
    logs = TransferLogSerializer(many=True, read_only=True)
    
    class Meta:
        model = Transfer
        fields = [
            'id', 'transfer_id', 'sender', 'sender_email', 'recipient',
            'recipient_details', 'transfer_type', 'amount', 'currency',
            'fee', 'total_amount', 'status', 'description', 'reference_number',
            'requires_tac', 'tac_verified', 'tac_verified_at',
            'compliance_status', 'compliance_notes',
            'recipient_name', 'recipient_account', 'recipient_bank',
            'created_at', 'updated_at', 'completed_at', 'logs'
        ]
        read_only_fields = [
            'id', 'transfer_id', 'total_amount', 'sender',
            'created_at', 'updated_at', 'completed_at'
        ]


class TransferCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transfer
        fields = [
            'recipient', 'transfer_type', 'amount', 'currency',
            'description', 'recipient_name', 'recipient_account', 'recipient_bank'
        ]
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value
    
    def validate(self, data):
        # Check if recipient exists or manual details provided
        if not data.get('recipient'):
            if not data.get('recipient_name') or not data.get('recipient_account'):
                raise serializers.ValidationError(
                    "Either select a saved recipient or provide recipient details (name and account)."
                )
        return data


class TACCodeSerializer(serializers.ModelSerializer):
    is_valid = serializers.SerializerMethodField()
    
    class Meta:
        model = TACCode
        fields = ['id', 'code', 'is_used', 'expires_at', 'created_at', 'is_valid']
        read_only_fields = ['id', 'code', 'is_used', 'created_at']
    
    def get_is_valid(self, obj):
        return obj.is_valid()


class TACVerifySerializer(serializers.Serializer):
    transfer_id = serializers.CharField()
    tac_code = serializers.CharField(max_length=6, min_length=6)
    
    def validate_tac_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("TAC code must be 6 digits.")
        return value