"""
Django REST Framework serializers for Cards app
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Card, Transaction, CardType, CardStatus


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class CardSerializer(serializers.ModelSerializer):
    """Serializer for Card model"""
    
    user = UserSerializer(read_only=True)
    masked_number = serializers.ReadOnlyField()
    
    class Meta:
        model = Card
        fields = [
            'id', 'user', 'card_type', 'card_number', 'last_four',
            'cvv', 'expiry_date', 'cardholder_name', 'balance',
            'spending_limit', 'status', 'color_scheme', 'is_primary',
            'created_at', 'updated_at', 'masked_number'
        ]
        read_only_fields = [
            'id', 'user', 'card_number', 'last_four', 'cvv',
            'expiry_date', 'balance', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'card_number': {'write_only': True},
            'cvv': {'write_only': True}
        }


class CardCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new cards"""
    
    class Meta:
        model = Card
        fields = [
            'card_type', 'cardholder_name', 'spending_limit', 'color_scheme'
        ]


class CardUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating cards"""
    
    class Meta:
        model = Card
        fields = ['spending_limit', 'status', 'is_primary']


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction model"""
    
    user = UserSerializer(read_only=True)
    card_last_four = serializers.CharField(source='card.last_four', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'user', 'card', 'card_last_four', 'amount',
            'merchant', 'category', 'transaction_type', 'status',
            'description', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']


class TransactionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating transactions"""
    
    class Meta:
        model = Transaction
        fields = [
            'card', 'amount', 'merchant', 'category',
            'transaction_type', 'description'
        ]


class CardBalanceSerializer(serializers.Serializer):
    """Serializer for card balance information"""
    
    card_balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    account_balance = serializers.DecimalField(max_digits=10, decimal_places=2)


class TopUpSerializer(serializers.Serializer):
    """Serializer for card top-up"""
    
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01
    )
