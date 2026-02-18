"""
compliance/serializers.py - Serializers for compliance API
"""
from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal
import json

from .models import TransferRequest, TransferLog, ComplianceSetting


class TransferCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating transfer requests"""

    class Meta:
        model = TransferRequest
        fields = [
            'id',           #  ADDED
            'reference',    #  ADDED
            'amount',
            'recipient_name',
            'destination_type',
            'destination_details',
            'narration',
            'status',       #  ADDED (helpful for frontend)
            'requires_kyc'  #  ADDED (helpful for frontend)
        ]
        read_only_fields = ['id', 'reference', 'status', 'requires_kyc']  #  ADDED

    def validate_amount(self, value):
        if value <= Decimal('0.00'):
            raise serializers.ValidationError("Amount must be positive")

        # Check KYC threshold
        if value >= Decimal('1500.00'):
            # KYC will be required
            pass

        return value

    def validate_destination_details(self, value):
        """Validate destination details based on type"""
        destination_type = self.initial_data.get('destination_type')

        if not isinstance(value, dict):
            try:
                value = json.loads(value)
            except:
                raise serializers.ValidationError("Destination details must be valid JSON")

        if destination_type == 'bank':
            required = ['bank_name', 'account_number', 'account_type']
            for field in required:
                if field not in value:
                    raise serializers.ValidationError(f"Bank transfers require '{field}'")

        elif destination_type == 'mobile_wallet':
            required = ['provider', 'phone_number']
            for field in required:
                if field not in value:
                    raise serializers.ValidationError(f"Mobile wallet requires '{field}'")

        elif destination_type == 'crypto':
            required = ['currency', 'wallet_address']
            for field in required:
                if field not in value:
                    raise serializers.ValidationError(f"Crypto requires '{field}'")

        return value


class TransferSerializer(serializers.ModelSerializer):
    """Basic transfer serializer"""

    account_number = serializers.CharField(source='account.account_number', read_only=True)
    account_email = serializers.CharField(source='account.email', read_only=True)  #  FIXED: removed .user
    destination_display = serializers.SerializerMethodField()

    class Meta:
        model = TransferRequest
        fields = [
            'id',
            'reference',
            'account_number',
            'account_email',
            'amount',
            'recipient_name',
            'destination_type',
            'destination_display',
            'destination_details',
            'status',
            'requires_kyc',
            'kyc_verified',
            'tac_code',
            'tac_generated_at',
            'tac_expires_at',
            'tac_sent_at',
            'tac_verified_at',
            'external_reference',
            'narration',
            'created_at'
        ]
        read_only_fields = ['reference', 'status', 'tac_code', 'created_at']

    def get_destination_display(self, obj):
        """Format destination for display"""
        details = obj.destination_details

        if obj.destination_type == 'bank':
            bank = details.get('bank_name', 'Bank')
            account = details.get('account_number', '')
            return f"{bank} - ****{account[-4:] if len(account) >= 4 else account}"

        elif obj.destination_type == 'mobile_wallet':
            provider = details.get('provider', 'Mobile')
            phone = details.get('phone_number', '')
            return f"{provider} - {phone}"

        elif obj.destination_type == 'crypto':
            currency = details.get('currency', 'Crypto')
            address = details.get('wallet_address', '')
            return f"{currency} - {address[:8]}..."

        return "Unknown"


class TransferDetailSerializer(TransferSerializer):
    """Detailed transfer serializer"""

    logs = serializers.SerializerMethodField()

    class Meta(TransferSerializer.Meta):
        fields = TransferSerializer.Meta.fields + ['logs']

    def get_logs(self, obj):
        """Get transfer logs"""
        logs = obj.logs.all().order_by('created_at')
        return TransferLogSerializer(logs, many=True).data


class TACVerificationSerializer(serializers.Serializer):
    """Serializer for TAC verification"""

    tac_code = serializers.CharField(max_length=6, min_length=6, required=True)

    def validate_tac_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("TAC must contain only digits")
        return value


class TransferStatusSerializer(serializers.ModelSerializer):
    """ FIXED: Serializer for transfer status"""

    tac_generated = serializers.SerializerMethodField()
    next_steps = serializers.SerializerMethodField()

    class Meta:
        model = TransferRequest
        fields = [
            'id',
            'reference',
            'status',
            'amount',
            'recipient_name',
            'destination_type',
            'destination_details',
            'narration',
            'created_at',
            'updated_at',
            'tac_generated',
            'tac_expires_at',
            'requires_kyc',
            'kyc_verified',
            'external_reference',
            'next_steps'
        ]

    def get_tac_generated(self, obj):
        """Return True if TAC has been generated"""
        return bool(obj.tac_code)

    def get_next_steps(self, obj):
        """Get next steps based on status"""
        if obj.status == 'pending_tac':
            return ['Admin will generate TAC code', 'You will receive TAC via email/SMS']
        elif obj.status == 'tac_generated':
            return ['TAC generated, awaiting admin to send']
        elif obj.status == 'tac_sent':
            return ['TAC sent, please enter code in dashboard', 'TAC expires in 24 hours']
        elif obj.status == 'tac_verified':
            return ['TAC verified, funds will be deducted', 'Admin will process bank transfer']
        elif obj.status == 'pending_settlement':
            return ['Funds deducted, awaiting bank transfer', 'Processing time: 1-2 business days']
        elif obj.status == 'completed':
            return ['Transfer completed']
        elif obj.status == 'kyc_required':
            return ['KYC required for this amount', 'Please submit KYC documents']
        return []


class TransferHistorySerializer(serializers.ModelSerializer):
    """Serializer for transfer history"""

    destination_display = serializers.SerializerMethodField()

    class Meta:
        model = TransferRequest
        fields = [
            'reference',
            'amount',
            'recipient_name',
            'destination_display',
            'status',
            'created_at',
            'settled_at'
        ]

    def get_destination_display(self, obj):
        """Format destination for display"""
        details = obj.destination_details

        if obj.destination_type == 'bank':
            bank = details.get('bank_name', 'Bank')
            return f"{bank}"

        elif obj.destination_type == 'mobile_wallet':
            provider = details.get('provider', 'Mobile')
            return f"{provider}"

        elif obj.destination_type == 'crypto':
            currency = details.get('currency', 'Crypto')
            return f"{currency}"

        return obj.destination_type


class TransferLogSerializer(serializers.ModelSerializer):
    """Serializer for transfer logs"""

    class Meta:
        model = TransferLog
        fields = ['log_type', 'message', 'metadata', 'created_at', 'created_by']


class ComplianceSettingSerializer(serializers.ModelSerializer):
    """Serializer for compliance settings"""

    class Meta:
        model = ComplianceSetting
        fields = ['setting_type', 'value', 'description', 'is_active', 'updated_by', 'updated_at']
        read_only_fields = ['updated_at']
