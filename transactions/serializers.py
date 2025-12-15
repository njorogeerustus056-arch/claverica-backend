from rest_framework import serializers
from .models import Transaction, TransactionLog
from datetime import datetime

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'id', 'user_id', 'transaction_id', 'type', 'amount', 'currency',
            'merchant', 'category', 'status', 'description', 'reference',
            'account_number', 'transaction_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'transaction_id', 'created_at', 'updated_at']


class TransactionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'user_id', 'type', 'amount', 'currency', 'merchant', 
            'category', 'description', 'reference', 'account_number', 
            'transaction_date'
        ]
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        return value
    
    def create(self, validated_data):
        if 'transaction_date' not in validated_data:
            validated_data['transaction_date'] = datetime.now()
        validated_data['status'] = 'completed'
        return super().create(validated_data)


class TransactionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['status', 'description', 'category', 'merchant']


class TransactionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionLog
        fields = ['id', 'transaction', 'user_id', 'action', 'details', 
                  'ip_address', 'user_agent', 'timestamp']
        read_only_fields = ['id', 'timestamp']


class TransactionStatsSerializer(serializers.Serializer):
    total_transactions = serializers.IntegerField()
    total_credits = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_debits = serializers.DecimalField(max_digits=15, decimal_places=2)
    net_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    pending_count = serializers.IntegerField()
    completed_count = serializers.IntegerField()
    failed_count = serializers.IntegerField()
    category_breakdown = serializers.DictField()
