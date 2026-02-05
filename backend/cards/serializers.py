"""
cards/serializers.py - FIXED VERSION
"""
from rest_framework import serializers
from .models import Card, CardTransaction
from django.utils import timezone
from decimal import Decimal
import re


class CardSerializer(serializers.ModelSerializer):
    """Card model serializer - FIXED"""
    brand = serializers.SerializerMethodField()
    masked_number = serializers.CharField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    can_spend = serializers.BooleanField(read_only=True)
    formatted_balance = serializers.CharField(read_only=True)

    # Account information
    account_number = serializers.CharField(read_only=True)
    full_name = serializers.CharField(read_only=True)

    # Balance from Wallet (read-only)
    balance = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    def get_brand(self, obj):
        """Determine card brand from number"""
        if hasattr(obj, 'card_number') and obj.card_number:
            if obj.card_number.startswith('4'):
                return 'Visa'
            elif obj.card_number.startswith('5'):
                return 'Mastercard'
        return 'Visa'

    class Meta:
        model = Card
        fields = [
            'id', 'card_type', 'brand', 'masked_number', 'last_four',
            'expiry_date', 'cardholder_name',
            'balance', 'formatted_balance',
            'account_number', 'full_name',
            'status', 'color_scheme', 'is_primary', 'created_at',
            'is_expired', 'can_spend'
        ]
        read_only_fields = ['last_four', 'created_at', 'masked_number',
                           'balance', 'account_number', 'full_name']

    def validate_cardholder_name(self, value):
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Cardholder name must be at least 2 characters long")
        return value.strip()

    def validate_expiry_date(self, value):
        if not re.match(r'^\d{2}/\d{2}$', value):
            raise serializers.ValidationError("Expiry date must be in MM/YY format")

        month, year = value.split('/')
        current_year = timezone.now().year % 100
        current_month = timezone.now().month

        if int(year) < current_year or (int(year) == current_year and int(month) < current_month):
            raise serializers.ValidationError("Card is expired")
        return value


class CardCreateSerializer(serializers.ModelSerializer):
    """Card creation serializer"""
    class Meta:
        model = Card
        fields = ['cardholder_name', 'color_scheme', 'is_primary']


class CardUpdateSerializer(serializers.ModelSerializer):
    """Card update serializer"""
    class Meta:
        model = Card
        fields = ['cardholder_name', 'color_scheme', 'status', 'is_primary']


class CardTransactionSerializer(serializers.ModelSerializer):
    """Serializer for card transactions"""
    class Meta:
        model = CardTransaction
        fields = '__all__'


class CardTransactionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating card transactions"""
    class Meta:
        model = CardTransaction
        fields = ['amount', 'merchant', 'category', 'transaction_type', 'description']


class CardBalanceSerializer(serializers.Serializer):
    """Serializer for card balance"""
    card_balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    wallet_balance = serializers.DecimalField(max_digits=10, decimal_places=2)


class TopUpSerializer(serializers.Serializer):
    """Serializer for card top-up - FIXED Decimal warning"""
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01')  # ✅ FIXED: Use Decimal instead of float
    )