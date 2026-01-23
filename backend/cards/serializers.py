"""
cards/serializers.py - CORRECTED VERSION
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Card, CardTransaction, CardType, CardStatus
from decimal import Decimal

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class CardSerializer(serializers.ModelSerializer):
    """Serializer for Card model"""
    
    user = UserSerializer(read_only=True)
    masked_number = serializers.ReadOnlyField()
    card_type_display = serializers.CharField(source='get_card_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Card
        fields = [
            'id', 'user', 'card_type', 'card_type_display', 'card_number', 'last_four',
            'masked_number', 'expiry_date', 'cardholder_name', 'balance',
            'spending_limit', 'status', 'status_display', 'color_scheme', 'is_primary',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'last_four', 'masked_number',
            'expiry_date', 'balance', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'card_number': {'write_only': True},
        }


class CardCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new cards"""
    
    class Meta:
        model = Card
        fields = [
            'card_type', 'cardholder_name', 'spending_limit', 'color_scheme'
        ]
    
    def validate_spending_limit(self, value):
        if value <= Decimal('0.00'):
            raise serializers.ValidationError("Spending limit must be greater than zero.")
        return value


class CardUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating cards"""
    
    class Meta:
        model = Card
        fields = ['spending_limit', 'status', 'is_primary']
    
    def validate_spending_limit(self, value):
        if value <= Decimal('0.00'):
            raise serializers.ValidationError("Spending limit must be greater than zero.")
        return value


class CardTransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction model"""
    
    user = UserSerializer(read_only=True)
    card_last_four = serializers.CharField(source='card.last_four', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = CardTransaction
        fields = [
            'id', 'user', 'card', 'card_last_four', 'amount',
            'merchant', 'category', 'transaction_type', 'transaction_type_display',
            'status', 'status_display', 'description', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']


class CardTransactionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating transactions"""
    
    class Meta:
        model = CardTransaction
        fields = [
            'card', 'amount', 'merchant', 'category',
            'transaction_type', 'description'
        ]
    
    def validate_amount(self, value):
        if value <= Decimal('0.00'):
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value


class CardBalanceSerializer(serializers.Serializer):
    """Serializer for card balance information"""
    
    card_balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    account_balance = serializers.DecimalField(max_digits=10, decimal_places=2)


class TopUpSerializer(serializers.Serializer):
    """Serializer for card top-up"""
    
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01')
    )


class CardDetailSerializer(serializers.ModelSerializer):
    """Detailed card serializer with additional information"""
    
    masked_number = serializers.ReadOnlyField()
    recent_transactions = serializers.SerializerMethodField()
    
    class Meta:
        model = Card
        fields = [
            'id', 'card_type', 'masked_number', 'last_four',
            'expiry_date', 'cardholder_name', 'balance',
            'spending_limit', 'status', 'color_scheme', 'is_primary',
            'created_at', 'recent_transactions'
        ]
    
    def get_recent_transactions(self, obj):
        """Get recent transactions for this card"""
        transactions = obj.transactions.all()[:5]  # Last 5 transactions
        return CardTransactionSerializer(transactions, many=True).data