from django.contrib import admin
from .models import (
    Account, Transaction, Card, Beneficiary,
    SavingsGoal, CryptoWallet, Subscription, Payment
)


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('account_number', 'user', 'account_type', 'currency', 'balance', 'is_active', 'created_at')
    list_filter = ('account_type', 'currency', 'is_active', 'is_verified')
    search_fields = ('account_number', 'user__username', 'user__email')
    readonly_fields = ('account_number', 'created_at', 'updated_at')
    fieldsets = (
        ('Account Information', {
            'fields': ('user', 'account_number', 'account_type', 'currency')
        }),
        ('Balance', {
            'fields': ('balance', 'available_balance')
        }),
        ('Status', {
            'fields': ('is_active', 'is_verified')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_id', 'account', 'transaction_type', 'amount', 
        'currency', 'status', 'created_at'
    )
    list_filter = ('transaction_type', 'status', 'currency', 'created_at')
    search_fields = (
        'transaction_id', 'account__account_number', 
        'recipient_name', 'description', 'reference_number'
    )
    readonly_fields = ('transaction_id', 'created_at', 'completed_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('transaction_id', 'account', 'transaction_type', 'amount', 'currency', 'status')
        }),
        ('Recipient Information', {
            'fields': ('recipient_account', 'recipient_name', 'recipient_email'),
            'classes': ('collapse',)
        }),
        ('Additional Details', {
            'fields': ('description', 'reference_number', 'fee', 'exchange_rate')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of completed transactions
        if obj and obj.status == 'completed':
            return False
        return super().has_delete_permission(request, obj)


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('get_masked_number', 'cardholder_name', 'card_type', 'status', 'expiry_date', 'created_at')
    list_filter = ('card_type', 'status', 'created_at')
    search_fields = ('card_number', 'cardholder_name', 'account__account_number')
    readonly_fields = ('created_at',)
    
    def get_masked_number(self, obj):
        return f"**** **** **** {obj.card_number[-4:]}"
    get_masked_number.short_description = 'Card Number'
    
    def expiry_date(self, obj):
        return f"{obj.expiry_month:02d}/{obj.expiry_year}"
    expiry_date.short_description = 'Expiry'
    
    fieldsets = (
        ('Card Information', {
            'fields': ('account', 'card_type', 'cardholder_name', 'card_number')
        }),
        ('Security', {
            'fields': ('cvv', 'expiry_month', 'expiry_year', 'status')
        }),
        ('Limits', {
            'fields': ('spending_limit',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Beneficiary)
class BeneficiaryAdmin(admin.ModelAdmin):
    list_display = ('name', 'account_number', 'user', 'country', 'currency', 'is_favorite', 'created_at')
    list_filter = ('country', 'currency', 'is_favorite', 'created_at')
    search_fields = ('name', 'account_number', 'email', 'user__username')
    readonly_fields = ('created_at',)


@admin.register(SavingsGoal)
class SavingsGoalAdmin(admin.ModelAdmin):
    list_display = ('name', 'account', 'progress_display', 'status', 'target_date', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'account__account_number', 'account__user__username')
    readonly_fields = ('created_at', 'completed_at', 'progress_percentage')
    date_hierarchy = 'created_at'
    
    def progress_display(self, obj):
        return f"{obj.current_amount}/{obj.target_amount} ({obj.progress_percentage:.1f}%)"
    progress_display.short_description = 'Progress'
    
    fieldsets = (
        ('Goal Information', {
            'fields': ('account', 'name', 'target_amount', 'current_amount', 'currency')
        }),
        ('Interest & Status', {
            'fields': ('interest_rate', 'status', 'target_date')
        }),
        ('Auto Deposit', {
            'fields': ('auto_deposit_amount', 'auto_deposit_frequency'),
            'classes': ('collapse',)
        }),
        ('Progress', {
            'fields': ('progress_percentage',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CryptoWallet)
class CryptoWalletAdmin(admin.ModelAdmin):
    list_display = ('crypto_type', 'account', 'balance', 'is_active', 'created_at')
    list_filter = ('crypto_type', 'is_active', 'created_at')
    search_fields = ('wallet_address', 'account__account_number', 'account__user__username')
    readonly_fields = ('wallet_address', 'created_at')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('service_name', 'account', 'amount', 'billing_cycle', 'next_billing_date', 'status')
    list_filter = ('billing_cycle', 'status', 'category', 'created_at')
    search_fields = ('service_name', 'merchant_name', 'account__account_number', 'account__user__username')
    readonly_fields = ('created_at',)
    date_hierarchy = 'next_billing_date'
    
    fieldsets = (
        ('Subscription Details', {
            'fields': ('account', 'service_name', 'merchant_name', 'category')
        }),
        ('Billing', {
            'fields': ('amount', 'currency', 'billing_cycle', 'next_billing_date', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Legacy payment model admin"""
    list_display = ('user', 'amount', 'transaction_type', 'status', 'timestamp')
    search_fields = ('user__username',)
    list_filter = ('transaction_type', 'status')
    readonly_fields = ('timestamp',)
