from django.contrib import admin
from .models import Wallet, Bank, Transaction, UserBankAccount

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    """Admin for Wallets"""
    list_display = ('account_number', 'account_email', 'balance', 'currency', 'created_at')
    search_fields = ('account__email', 'account__account_number')
    list_filter = ('currency', 'created_at')

    def account_number(self, obj):
        return obj.account.account_number
    account_number.short_description = 'Account Number'

    def account_email(self, obj):
        return obj.account.email
    account_email.short_description = 'Account Email'

@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    """Admin for Banks"""
    list_display = ('name', 'code', 'country', 'transfer_fee', 'is_active')
    list_filter = ('country', 'is_active')
    search_fields = ('name', 'code', 'country')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin for Transactions"""
    list_display = ('id', 'wallet', 'transaction_type', 'amount', 'timestamp')
    list_filter = ('transaction_type', 'timestamp')
    search_fields = ('wallet__account__account_number', 'reference', 'description')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('wallet', 'transaction_type', 'amount', 'reference', 'description')
        }),
        ('Balance Information', {
            'fields': ('balance_before', 'balance_after'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        })
    )

@admin.register(UserBankAccount)
class UserBankAccountAdmin(admin.ModelAdmin):
    """Admin for User Bank Accounts"""
    list_display = ('account_name', 'account_number', 'bank', 'is_verified', 'is_default', 'created_at')
    list_filter = ('is_verified', 'is_default', 'bank', 'created_at')
    search_fields = ('account_name', 'account_number', 'account__account_number')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Account Information', {
            'fields': ('account', 'bank', 'account_name', 'account_number', 'branch')
        }),
        ('Verification', {
            'fields': ('is_verified', 'is_default'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )