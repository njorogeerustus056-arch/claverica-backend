"""
transfers/serializers.py - Updated with compliance integration
"""

from rest_framework import serializers
from django.utils import timezone
from django.core.validators import MinValueValidator

from backend.compliance.serializers import ComplianceRequestSerializer, KYCVerificationSerializer
from backend.compliance.models import ComplianceProfile
from .models import Transfer, TransferLog, TransferLimit
from .services import TransferComplianceService


class TransferCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating transfers with compliance check"""
    
    class Meta:
        model = Transfer
        fields = [
            'recipient_name',
            'recipient_account',
            'recipient_bank',
            'recipient_country',
            'recipient_phone',
            'recipient_email',
            'amount',
            'currency',
            'description',
            'reference',
        ]
        extra_kwargs = {
            'amount': {'validators': [MinValueValidator(0.01)]},
        }
    
    def validate(self, data):
        # Check user's KYC status
        user = self.context['request'].user
        
        try:
            profile = ComplianceProfile.objects.get(user=user)
            if profile.kyc_status != 'approved':
                raise serializers.ValidationError("KYC verification required before making transfers")
        except ComplianceProfile.DoesNotExist:
            raise serializers.ValidationError("Compliance profile not found. Please complete KYC verification.")
        
        # Check transfer limits
        limit_violations = TransferComplianceService.check_transfer_limits(
            user=user,
            amount=data['amount'],
            currency=data.get('currency', 'USD'),
            country=data.get('recipient_country')
        )
        
        if limit_violations:
            raise serializers.ValidationError(limit_violations[0])
        
        return data
    
    def create(self, validated_data):
        user = self.context['request'].user
        
        # Create transfer
        transfer = Transfer.objects.create(
            user=user,
            **validated_data
        )
        
        # Create audit log
        TransferLog.objects.create(
            transfer=transfer,
            log_type='created',
            message=f"Transfer created for {transfer.amount} {transfer.currency}",
            created_by=user
        )
        
        # Perform compliance assessment
        try:
            TransferComplianceService.assess_transfer_risk(transfer)
        except Exception as e:
            # Log error but don't fail creation
            TransferLog.objects.create(
                transfer=transfer,
                log_type='compliance_check',
                message=f"Compliance assessment failed: {str(e)}",
                created_by=user
            )
        
        return transfer


class TransferUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating transfers"""
    
    class Meta:
        model = Transfer
        fields = [
            'description',
            'notes',
            'status',
        ]
        read_only_fields = ['status']
    
    def validate_status(self, value):
        valid_transitions = {
            'draft': ['pending', 'cancelled'],
            'pending': ['processing', 'cancelled'],
            'awaiting_tac': ['pending', 'cancelled'],
            'awaiting_video_call': ['pending', 'cancelled'],
            'compliance_review': ['pending', 'cancelled'],
        }
        
        current_status = self.instance.status
        if current_status not in valid_transitions or value not in valid_transitions[current_status]:
            raise serializers.ValidationError(f"Cannot transition from {current_status} to {value}")
        
        return value


class TransferSerializer(serializers.ModelSerializer):
    """Full transfer serializer with compliance info"""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    compliance_request = ComplianceRequestSerializer(read_only=True)
    kyc_status = serializers.SerializerMethodField()
    logs = serializers.SerializerMethodField()
    
    class Meta:
        model = Transfer
        fields = [
            'transfer_id',
            'user',
            'user_email',
            'user_name',
            'amount',
            'currency',
            'recipient_name',
            'recipient_account',
            'recipient_bank',
            'recipient_country',
            'recipient_phone',
            'recipient_email',
            'status',
            'priority',
            'risk_level',
            'compliance_request',
            'tac_required',
            'tac_verified',
            'tac_verified_at',
            'video_call_required',
            'video_call_completed',
            'kyc_status',
            'description',
            'reference',
            'notes',
            'fee',
            'tax',
            'total_amount',
            'created_at',
            'updated_at',
            'submitted_at',
            'processed_at',
            'completed_at',
            'logs',
        ]
        read_only_fields = [
            'transfer_id', 'user', 'risk_level', 'tac_required', 
            'video_call_required', 'fee', 'tax', 'total_amount'
        ]
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email
    
    def get_kyc_status(self, obj):
        try:
            profile = ComplianceProfile.objects.get(user=obj.user)
            return profile.kyc_status
        except ComplianceProfile.DoesNotExist:
            return 'not_started'
    
    def get_logs(self, obj):
        from .serializers import TransferLogSerializer
        logs = obj.logs.all()[:10]  # Last 10 logs
        return TransferLogSerializer(logs, many=True).data


class TransferLogSerializer(serializers.ModelSerializer):
    """Serializer for transfer logs"""
    
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True, allow_null=True)
    
    class Meta:
        model = TransferLog
        fields = [
            'id',
            'log_type',
            'message',
            'metadata',
            'created_by',
            'created_by_email',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class TransferLimitSerializer(serializers.ModelSerializer):
    """Serializer for transfer limits"""
    
    class Meta:
        model = TransferLimit
        fields = [
            'id',
            'user',
            'country',
            'currency',
            'limit_type',
            'amount',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TACVerificationSerializer(serializers.Serializer):
    """Serializer for TAC verification"""
    
    tac_code = serializers.CharField(max_length=6, min_length=6, required=True)
    transfer_id = serializers.CharField(max_length=50, required=True)
    
    def validate(self, data):
        transfer_id = data['transfer_id']
        
        try:
            transfer = Transfer.objects.get(transfer_id=transfer_id)
        except Transfer.DoesNotExist:
            raise serializers.ValidationError("Transfer not found")
        
        # Check if transfer belongs to user
        user = self.context['request'].user
        if transfer.user != user:
            raise serializers.ValidationError("Permission denied")
        
        # Check if TAC is required
        if not transfer.tac_required:
            raise serializers.ValidationError("TAC verification not required for this transfer")
        
        # Check if already verified
        if transfer.tac_verified:
            raise serializers.ValidationError("TAC already verified")
        
        data['transfer'] = transfer
        return data


class TransferStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating transfer status"""
    
    status = serializers.ChoiceField(choices=Transfer.TRANSFER_STATUS_CHOICES)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        transfer = self.context['transfer']
        
        valid_transitions = {
            'draft': ['pending', 'cancelled'],
            'pending': ['processing', 'cancelled'],
            'processing': ['completed', 'failed'],
            'awaiting_tac': ['pending', 'cancelled'],
            'awaiting_video_call': ['pending', 'cancelled'],
            'compliance_review': ['pending', 'cancelled'],
        }
        
        current_status = transfer.status
        new_status = data['status']
        
        if current_status not in valid_transitions or new_status not in valid_transitions[current_status]:
            raise serializers.ValidationError(f"Cannot transition from {current_status} to {new_status}")
        
        return data


class TransferDashboardSerializer(serializers.Serializer):
    """Serializer for transfer dashboard"""
    
    total_transfers = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    pending_transfers = serializers.IntegerField()
    completed_transfers = serializers.IntegerField()
    failed_transfers = serializers.IntegerField()
    average_transfer_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    recent_transfers = TransferSerializer(many=True)