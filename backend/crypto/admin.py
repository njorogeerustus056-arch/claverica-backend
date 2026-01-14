# crypto/admin.py - UPDATED FOR COMPLIANCE

from django.contrib import admin
from .models import (
    CryptoAsset, CryptoWallet, CryptoTransaction,
    PriceHistory, CryptoAddress, FiatPlatform, UserFiatAccount,
    CryptoComplianceFlag, CryptoAuditLog
)


@admin.register(CryptoAsset)
class CryptoAssetAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'name', 'blockchain', 'current_price_usd', 'is_active']
    list_filter = ['blockchain', 'is_active', 'is_tradable']
    search_fields = ['symbol', 'name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CryptoWallet)
class CryptoWalletAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'asset', 'balance', 'balance_usd', 'is_active',
        'compliance_status', 'requires_compliance_approval'  # NEW
    ]
    list_filter = [
        'wallet_type', 'is_active', 
        'compliance_status', 'requires_compliance_approval'  # NEW
    ]
    search_fields = [
        'user__email', 'asset__symbol', 'wallet_address',
        'compliance_reference'  # NEW
    ]
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CryptoTransaction)
class CryptoTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'asset', 'transaction_type', 'status', 
        'amount', 'amount_usd', 'compliance_status',  # NEW
        'requires_compliance_approval', 'created_at'  # NEW
    ]
    list_filter = [
        'transaction_type', 'status', 'compliance_status',  # NEW
        'requires_compliance_approval', 'is_high_value', 'is_suspicious'  # NEW
    ]
    search_fields = [
        'user__email', 'asset__symbol', 'transaction_hash',
        'compliance_reference'  # NEW
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'completed_at', 'confirmed_at',
        'compliance_reference'  # NEW
    ]


@admin.register(CryptoComplianceFlag)
class CryptoComplianceFlagAdmin(admin.ModelAdmin):
    list_display = [
        'transaction', 'flag_type', 'priority', 'is_resolved',
        'created_at'
    ]
    list_filter = ['flag_type', 'priority', 'is_resolved']
    search_fields = [
        'transaction__id', 'transaction__asset__symbol',
        'description'
    ]
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CryptoAuditLog)
class CryptoAuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'transaction', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['user__email', 'action', 'details']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'


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