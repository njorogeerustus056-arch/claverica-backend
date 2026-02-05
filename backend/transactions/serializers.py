from rest_framework import serializers
from .models import Wallet, Transaction, UserBankAccount, Bank

class WalletSerializer(serializers.ModelSerializer):
    account_number = serializers.CharField(source='account.account_number', read_only=True)
    email = serializers.EmailField(source='account.email', read_only=True)
    
    class Meta:
        model = Wallet
        fields = [
            'id', 'account_number', 'email', 'balance', 'currency',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'account_number', 'email', 'created_at', 'updated_at']

class TransactionSerializer(serializers.ModelSerializer):
    account_number = serializers.CharField(source='wallet.account.account_number', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'account_number', 'transaction_type', 'amount',
            'reference', 'description', 'balance_before', 'balance_after',
            'metadata', 'timestamp'
        ]
        read_only_fields = ['id', 'account_number', 'timestamp']

class BankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bank
        fields = ['id', 'name', 'code', 'country', 'transfer_fee', 'is_active']

class UserBankAccountSerializer(serializers.ModelSerializer):
    bank_details = BankSerializer(source='bank', read_only=True)
    account_number_display = serializers.CharField(source='account.account_number', read_only=True)
    
    class Meta:
        model = UserBankAccount
        fields = [
            'id', 'account_number_display', 'bank', 'bank_details',
            'account_name', 'account_number', 'branch', 'is_verified',
            'is_default', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate(self, data):
        # Ensure user doesn't add duplicate bank accounts
        if UserBankAccount.objects.filter(
            account=data['account'],
            bank=data['bank'],
            account_number=data['account_number']
        ).exists():
            raise serializers.ValidationError(
                'This bank account is already registered for this user'
            )
        return data

class CreditDebitSerializer(serializers.Serializer):
    account_number = serializers.CharField(max_length=50, required=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    reference = serializers.CharField(max_length=100, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        return value
