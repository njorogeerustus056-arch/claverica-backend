from django.contrib import admin
from .models import (
    CryptoAsset, CryptoWallet, CryptoTransaction,
    PriceHistory, CryptoAddress, FiatPlatform, UserFiatAccount
)


@admin.register(CryptoAsset)
class CryptoAssetAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'name', 'blockchain', 'current_price_usd', 'is_active']
    list_filter = ['blockchain', 'is_active', 'is_tradable']
    search_fields = ['symbol', 'name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CryptoWallet)
class CryptoWalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'asset', 'balance', 'balance_usd', 'is_active']
    list_filter = ['wallet_type', 'is_active']
    search_fields = ['user__email', 'asset__symbol', 'wallet_address']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CryptoTransaction)
class CryptoTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'asset', 'transaction_type', 'status', 'amount', 'created_at']
    list_filter = ['transaction_type', 'status']
    search_fields = ['user__email', 'asset__symbol', 'transaction_hash']
    readonly_fields = ['created_at', 'updated_at', 'completed_at', 'confirmed_at']


@admin.register(CryptoAddress)
class CryptoAddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'asset', 'address', 'is_verified', 'created_at']
    list_filter = ['is_verified', 'address_type']
    search_fields = ['user__email', 'asset__symbol', 'address']
    readonly_fields = ['created_at', 'updated_at', 'verified_at']


@admin.register(FiatPlatform)
class FiatPlatformAdmin(admin.ModelAdmin):
    list_display = ['name', 'platform_type', 'supports_deposits', 'supports_withdrawals', 'is_active']
    list_filter = ['platform_type', 'is_active']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(UserFiatAccount)
class UserFiatAccountAdmin(admin.ModelAdmin):
    list_display = ['user', 'platform', 'currency', 'balance', 'is_verified', 'is_active']
    list_filter = ['currency', 'is_verified', 'is_active']
    search_fields = ['user__email', 'platform__name', 'account_number']
    readonly_fields = ['created_at', 'updated_at', 'verified_at']