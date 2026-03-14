"""
Transfer Serializers - Data serialization for transfer operations
"""

from rest_framework import serializers
from django.utils import timezone
from django.core.validators import MinValueValidator

from .models import Transfer, TAC, TransferLog, TransferLimit


class TransferCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new transfers"""

    class Meta:
        model = Transfer
        fields = [
            'recipient_name',
            'destination_type',
            'destination_details',
            'amount',
            'narration',
        ]
        extra_kwargs = {
            'amount': {'validators': [MinValueValidator(0.01)]},
            'destination_details': {'required': True},
        }

    def validate_destination_details(self, value):
        """Validate destination details based on type"""
        destination_type = self.initial_data.get('destination_type')

        if destination_type == 'bank':
            required_fields = ['bank_name', 'account_number', 'account_type']
            for field in required_fields:
                if field not in value:
                    raise serializers.ValidationError(
                        f"Bank transfers require '{field}' field"
                    )

        elif destination_type == 'mobile_wallet':
            required_fields = ['mobile_provider', 'mobile_number']
            for field in required_fields:
                if field not in value:
                    raise serializers.ValidationError(
                        f"Mobile wallet transfers require '{field}' field"
                    )

        elif destination_type == 'mobile_money':
            required_fields = ['mobile_money_provider', 'mobile_money_number']
            for field in required_fields:
                if field not in value:
                    raise serializers.ValidationError(
                        f"Mobile money transfers require '{field}' field"
                    )

        # 👇 ADDED e_wallet validation
        elif destination_type == 'e_wallet':
            required_fields = ['provider', 'email']
            for field in required_fields:
                if field not in value:
                    raise serializers.ValidationError(
                        f"E-wallet transfers require '{field}' field"
                    )
            # Optional email validation
            if 'email' in value and '@' not in value['email']:
                raise serializers.ValidationError("Invalid email format")

        elif destination_type == 'crypto':
            required_fields = ['crypto_type', 'crypto_address']
            for field in required_fields:
                if field not in value:
                    raise serializers.ValidationError(
                        f"Crypto transfers require '{field}' field"
                    )

        return value


class TransferSerializer(serializers.ModelSerializer):
    """Serializer for basic transfer data"""

    account_number = serializers.CharField(source='account.account_number', read_only=True)
    account_email = serializers.CharField(source='account.email', read_only=True)
    destination_display = serializers.SerializerMethodField()
    tac_status = serializers.SerializerMethodField()

    class Meta:
        model = Transfer
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
            'tac_status',
            'narration',
            'created_at',
            'tac_sent_at',
            'tac_verified_at',
            'deducted_at',
            'settled_at',
            'external_reference',
        ]
        read_only_fields = ['reference', 'created_at', 'tac_sent_at',
                          'tac_verified_at', 'deducted_at', 'settled_at']

    def get_destination_display(self, obj):
        """Get formatted destination display"""
        details = obj.destination_details

        if obj.destination_type == 'bank':
            account_num = details.get('account_number', '')
            masked = f"****{account_num[-4:]}" if len(account_num) >= 4 else account_num
            return f"{details.get('bank_name', 'Bank')} - {masked}"

        elif obj.destination_type == 'mobile_wallet':
            return f"{details.get('mobile_provider', 'Mobile')} - {details.get('mobile_number', '')}"

        elif obj.destination_type == 'mobile_money':
            return f"{details.get('mobile_money_provider', 'Mobile Money')} - {details.get('mobile_money_number', '')}"

        # 👇 ADDED e_wallet display
        elif obj.destination_type == 'e_wallet':
            return f"{details.get('provider', 'E-Wallet')} - {details.get('email', '')}"

        elif obj.destination_type == 'crypto':
            address = details.get('crypto_address', '')
            short_addr = f"{address[:8]}..." if len(address) > 8 else address
            return f"{details.get('crypto_type', 'Crypto')} - {short_addr}"

        return "Unknown destination"

    def get_tac_status(self, obj):
        """Get TAC status if available"""
        if hasattr(obj, 'tac'):
            return {
                'code': obj.tac.code if self.context.get('is_admin', False) else '******',
                'status': obj.tac.status,
                'expires_at': obj.tac.expires_at,
                'is_valid': obj.tac.is_valid(),
            }
        return None


class TransferDetailSerializer(TransferSerializer):
    """Serializer for detailed transfer view"""

    logs = serializers.SerializerMethodField()

    class Meta(TransferSerializer.Meta):
        fields = TransferSerializer.Meta.fields + ['logs', 'admin_notes']

    def get_logs(self, obj):
        """Get transfer logs"""
        logs = obj.logs.all().order_by('-created_at')[:10]
        return TransferLogSerializer(logs, many=True).data


class TACVerificationSerializer(serializers.Serializer):
    """Serializer for TAC verification"""

    tac_code = serializers.CharField(max_length=6, min_length=6, required=True)

    def validate_tac_code(self, value):
        """Validate TAC code format"""
        if not value.isdigit():
            raise serializers.ValidationError("TAC code must contain only digits")
        return value


class TransferSettlementSerializer(serializers.Serializer):
    """Serializer for marking transfer as settled"""

    external_reference = serializers.CharField(max_length=100, required=True)
    admin_notes = serializers.CharField(required=False, allow_blank=True)


class TransferCancelSerializer(serializers.Serializer):
    """Serializer for cancelling transfers"""

    reason = serializers.CharField(required=True)


class TransferLimitSerializer(serializers.ModelSerializer):
    """Serializer for transfer limits"""

    class Meta:
        model = TransferLimit
        fields = ['id', 'limit_type', 'amount', 'is_active', 'created_at']
        read_only_fields = ['created_at']


class TransferLogSerializer(serializers.ModelSerializer):
    """Serializer for transfer logs"""

    class Meta:
        model = TransferLog
        fields = ['id', 'log_type', 'message', 'metadata', 'created_at']
        read_only_fields = fields


class TransferDashboardSerializer(serializers.Serializer):
    """Serializer for transfer dashboard data"""

    total_count = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    today_count = serializers.IntegerField()
    today_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    pending_count = serializers.IntegerField()
    pending_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    completed_count = serializers.IntegerField()
    completed_amount = serializers.DecimalField(max_digits=10, decimal_places=2)


class AdminTransferSerializer(TransferSerializer):
    """Serializer for admin transfer view"""

    class Meta(TransferSerializer.Meta):
        fields = TransferSerializer.Meta.fields + ['admin_notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add admin context to show full TAC code
        self.context['is_admin'] = True