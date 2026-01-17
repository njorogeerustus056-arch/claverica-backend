# crypto/admin.py - UPDATED FOR COMPLIANCE

from django.contrib import admin
from .models import (
    CryptoAsset, CryptoWallet, CryptoTransaction,
    CryptoComplianceFlag, CryptoAuditLog
    # REMOVED: PriceHistory, CryptoAddress, FiatPlatform, UserFiatAccount
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
        'compliance_status', 'requires_compliance_approval'
    ]
    list_filter = [
        'wallet_type', 'is_active', 
        'compliance_status', 'requires_compliance_approval'
    ]
    search_fields = [
        'user__email', 'asset__symbol', 'wallet_address',
        'compliance_reference'
    ]
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CryptoTransaction)
class CryptoTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'asset', 'transaction_type', 'status', 
        'amount', 'amount_usd', 'compliance_status',
        'requires_compliance_approval', 'created_at'
    ]
    list_filter = [
        'transaction_type', 'status', 'compliance_status',
        'requires_compliance_approval', 'is_high_value', 'is_suspicious'
    ]
    search_fields = [
        'user__email', 'asset__symbol', 'transaction_hash',
        'compliance_reference'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'completed_at', 'confirmed_at',
        'compliance_reference'
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


# REMOVED: CryptoAddress, FiatPlatform, UserFiatAccount admin registrations
# because these models don't exist in your models.py