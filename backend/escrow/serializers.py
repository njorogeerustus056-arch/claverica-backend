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
            'dispute_opened_by', 'dispute_opened_at', 'expected_release_date',
            'funded_at', 'released_at', 'created_at', 'updated_at', 'metadata'
        ]
        read_only_fields = [
            'id', 'escrow_id', 'total_amount', 'created_at', 'updated_at',
            'funded_at', 'released_at'
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
            'ip_address', 'created_at'  # CHANGED: 'timestamp' to 'created_at'
        ]
        read_only_fields = ['id', 'created_at']  # CHANGED: 'timestamp' to 'created_at'

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