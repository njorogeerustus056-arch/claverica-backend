# escrow/serializers.py - UPDATED FOR COMPLIANCE INTEGRATION

from rest_framework import serializers
from .models import Escrow, EscrowLog
from decimal import Decimal

class EscrowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Escrow
        fields = [
            'id', 'escrow_id', 'sender_id', 'sender_name', 'receiver_id', 'receiver_name',
            'amount', 'currency', 'fee', 'total_amount', 'title', 'description',
            'terms_and_conditions', 'status', 'is_released', 'release_approved_by_sender',
            'release_approved_by_receiver', 'dispute_status', 'dispute_reason',
            'dispute_opened_by', 'dispute_opened_at', 'compliance_reference',  # NEW
            'requires_compliance_approval',  # NEW
            'expected_release_date', 'funded_at', 'released_at', 
            'created_at', 'updated_at', 'metadata'
        ]
        read_only_fields = [
            'id', 'escrow_id', 'total_amount', 'created_at', 'updated_at',
            'funded_at', 'released_at', 'compliance_reference',  # NEW
            'requires_compliance_approval'  # NEW
        ]

class EscrowCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Escrow
        fields = [
            'sender_id', 'sender_name', 'receiver_id', 'receiver_name',
            'amount', 'currency', 'title', 'description', 'terms_and_conditions',
            'expected_release_date'
        ]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        return value

    def create(self, validated_data):
        amount = validated_data['amount']
        fee = amount * Decimal('0.02')
        validated_data['fee'] = fee
        validated_data['status'] = 'pending'
        return super().create(validated_data)

class EscrowUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Escrow
        fields = ['status', 'description', 'terms_and_conditions', 'expected_release_date']

class EscrowLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = EscrowLog
        fields = [
            'id', 'escrow', 'user_id', 'user_name', 'action', 'details',
            'ip_address', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class EscrowStatsSerializer(serializers.Serializer):
    total_escrows = serializers.IntegerField(min_value=0)
    active_escrows = serializers.IntegerField(min_value=0)
    completed_escrows = serializers.IntegerField(min_value=0)
    total_amount_in_escrow = serializers.DecimalField(
        max_digits=15, decimal_places=2, min_value=Decimal('0')
    )
    total_amount_released = serializers.DecimalField(
        max_digits=15, decimal_places=2, min_value=Decimal('0')
    )
    pending_disputes = serializers.IntegerField(min_value=0)

# NEW: Compliance Integration Serializers

class EscrowDisputeRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=500, required=True)
    details = serializers.JSONField(required=False, default=dict)

class EscrowTACVerificationSerializer(serializers.Serializer):
    tac_code = serializers.CharField(max_length=10, min_length=6, required=True)

class EscrowComplianceFormSerializer(serializers.Serializer):
    form_data = serializers.JSONField(required=True)

class ManualReleaseRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=500, required=True)
    supporting_docs = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=[]
    )

class ComplianceStatusSerializer(serializers.Serializer):
    escrow_id = serializers.IntegerField(required=True)