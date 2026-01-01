from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    CryptoAsset, CryptoWallet, CryptoTransaction,
    PriceHistory, CryptoAddress, FiatPlatform, UserFiatAccount
)

User = get_user_model()


class CryptoAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = CryptoAsset
        fields = [
            'id', 'symbol', 'name', 'logo', 'blockchain', 'contract_address',
            'current_price_usd', 'market_cap', 'volume_24h', 'change_24h',
            'change_7d', 'change_30d', 'is_tradable', 'is_depositable',
            'is_withdrawable', 'min_deposit', 'min_withdrawal', 'withdrawal_fee',
            'is_active', 'description', 'website', 'explorer_url',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CryptoWalletSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    asset_symbol = serializers.CharField(source='asset.symbol', read_only=True)
    asset_name = serializers.CharField(source='asset.name', read_only=True)
    asset_logo = serializers.CharField(source='asset.logo', read_only=True)
    current_price_usd = serializers.DecimalField(source='asset.current_price_usd', max_digits=20, decimal_places=8, read_only=True)
    
    class Meta:
        model = CryptoWallet
        fields = [
            'id', 'user', 'user_email', 'asset', 'asset_symbol', 'asset_name',
            'asset_logo', 'wallet_address', 'wallet_type', 'label',
            'balance', 'available_balance', 'locked_balance', 'balance_usd',
            'current_price_usd', 'is_active', 'is_verified', 'created_at',
            'updated_at', 'last_transaction_at'
        ]
        read_only_fields = [
            'id', 'user', 'balance_usd', 'created_at', 'updated_at',
            'last_transaction_at'
        ]


class CryptoTransactionSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    asset_symbol = serializers.CharField(source='asset.symbol', read_only=True)
    from_wallet_address = serializers.CharField(source='from_wallet.wallet_address', read_only=True, allow_null=True)
    to_wallet_address = serializers.CharField(source='to_wallet.wallet_address', read_only=True, allow_null=True)
    
    class Meta:
        model = CryptoTransaction
        fields = [
            'id', 'user', 'user_email', 'asset', 'asset_symbol',
            'transaction_type', 'status', 'from_wallet', 'from_wallet_address',
            'to_wallet', 'to_wallet_address', 'from_address', 'to_address',
            'amount', 'amount_usd', 'fee', 'fee_usd', 'network_fee',
            'price_at_transaction', 'transaction_hash', 'block_number',
            'confirmations', 'required_confirmations', 'gas_price',
            'gas_used', 'gas_limit', 'swap_from_asset', 'swap_to_asset',
            'swap_rate', 'error_message', 'description', 'ip_address',
            'user_agent', 'created_at', 'updated_at', 'completed_at',
            'confirmed_at'
        ]
        read_only_fields = [
            'id', 'user', 'amount_usd', 'created_at', 'updated_at',
            'completed_at', 'confirmed_at'
        ]


class CryptoTransactionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CryptoTransaction
        fields = [
            'asset', 'transaction_type', 'from_wallet', 'to_wallet',
            'from_address', 'to_address', 'amount', 'description'
        ]
    
    def validate(self, data):
        user = self.context['request'].user
        
        # Validate from_wallet belongs to user
        if data.get('from_wallet'):
            if data['from_wallet'].user != user:
                raise serializers.ValidationError({"from_wallet": "Wallet does not belong to user"})
            
            # Check balance for send/withdrawal transactions
            if data['transaction_type'] in ['send', 'withdrawal']:
                if data['from_wallet'].available_balance < data['amount']:
                    raise serializers.ValidationError({"amount": "Insufficient balance"})
        
        # Validate to_wallet belongs to user (if provided)
        if data.get('to_wallet'):
            if data['to_wallet'].user != user:
                raise serializers.ValidationError({"to_wallet": "Wallet does not belong to user"})
        
        return data


class CryptoAddressSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    asset_symbol = serializers.CharField(source='asset.symbol', read_only=True)
    
    class Meta:
        model = CryptoAddress
        fields = [
            'id', 'user', 'user_email', 'asset', 'asset_symbol',
            'address', 'label', 'address_type', 'is_verified',
            'is_whitelisted', 'verified_at', 'created_at',
            'updated_at', 'last_used_at'
        ]
        read_only_fields = ['id', 'user', 'verified_at', 'created_at', 'updated_at', 'last_used_at']


class FiatPlatformSerializer(serializers.ModelSerializer):
    class Meta:
        model = FiatPlatform
        fields = [
            'id', 'name', 'logo', 'platform_type', 'supported_currencies',
            'supported_countries', 'supports_deposits', 'supports_withdrawals',
            'deposit_fee', 'withdrawal_fee', 'min_deposit', 'max_deposit',
            'min_withdrawal', 'max_withdrawal', 'deposit_processing_time',
            'withdrawal_processing_time', 'is_active', 'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserFiatAccountSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    platform_name = serializers.CharField(source='platform.name', read_only=True)
    
    class Meta:
        model = UserFiatAccount
        fields = [
            'id', 'user', 'user_email', 'platform', 'platform_name',
            'account_number', 'account_holder', 'balance', 'currency',
            'is_verified', 'verified_at', 'is_active', 'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'user', 'verified_at', 'created_at', 'updated_at']


class UserFiatAccountCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFiatAccount
        fields = ['platform', 'account_number', 'account_holder', 'currency']
    
    def validate(self, data):
        user = self.context['request'].user
        
        # Check if account already exists
        if UserFiatAccount.objects.filter(
            user=user,
            platform=data['platform'],
            account_number=data.get('account_number')
        ).exists():
            raise serializers.ValidationError("This account is already linked")
        
        return data
    
    def create(self, validated_data):
        return UserFiatAccount.objects.create(
            user=self.context['request'].user,
            **validated_data
        )