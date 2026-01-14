# payments/admin.py - REMOVED COMPLIANCE MODELS

from django.contrib import admin
from .models import (
    Account, Transaction, Card, PaymentMethod, AuditLog,
    MainBusinessWallet, EmployeePlatformWallet, 
    PaymentTransactionNotification, WithdrawalRequest, ActivityFeed
    # REMOVED: ManualPaymentRelease, KYCVerification
)


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['account_number', 'user', 'account_type', 'balance', 'currency', 'is_active', 'created_at']
    list_filter = ['account_type', 'currency', 'is_active', 'is_verified']
    search_fields = ['account_number', 'user__email']
    readonly_fields = ['account_number', 'created_at', 'updated_at']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'account', 'transaction_type', 'amount', 'currency', 'status', 'created_at']
    list_filter = ['transaction_type', 'status', 'currency', 'requires_manual_approval']
    search_fields = ['transaction_id', 'account__account_number', 'description']
    readonly_fields = ['transaction_id', 'created_at', 'updated_at', 'completed_at']


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ['card_network', 'last_four', 'card_holder_name', 'account', 'status', 'is_default', 'is_expired']
    list_filter = ['card_network', 'card_type', 'status', 'is_default']
    search_fields = ['last_four', 'card_holder_name', 'account__account_number']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'user', 'method_type', 'is_default', 'created_at']
    list_filter = ['method_type', 'is_default']
    search_fields = ['display_name', 'user__email']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'model_name', 'created_at']
    list_filter = ['action', 'model_name', 'created_at']
    search_fields = ['user__email', 'action', 'model_name', 'object_id']
    readonly_fields = ['created_at']


@admin.register(MainBusinessWallet)
class MainBusinessWalletAdmin(admin.ModelAdmin):
    list_display = ['wallet_number', 'user', 'wallet_type', 'total_balance', 'available_balance', 'is_active', 'created_at']
    list_filter = ['wallet_type', 'is_active', 'auto_replenish']
    search_fields = ['wallet_number', 'user__email', 'display_name']
    readonly_fields = ['wallet_number', 'created_at', 'updated_at']


@admin.register(EmployeePlatformWallet)
class EmployeePlatformWalletAdmin(admin.ModelAdmin):
    list_display = ['wallet_number', 'user', 'platform_balance', 'available_for_withdrawal', 'status', 'last_withdrawal_date']
    list_filter = ['status', 'auto_withdraw_enabled']
    search_fields = ['wallet_number', 'user__email']
    readonly_fields = ['wallet_number', 'created_at', 'updated_at']


@admin.register(PaymentTransactionNotification)
class PaymentTransactionNotificationAdmin(admin.ModelAdmin):
    list_display = ['reference_code', 'notification_type', 'sender', 'receiver', 'amount', 'website_delivered', 'created_at']
    list_filter = ['notification_type', 'website_delivered', 'email_sent', 'push_sent']
    search_fields = ['reference_code', 'sender__email', 'receiver__email', 'short_message']
    readonly_fields = ['reference_code', 'created_at', 'delivered_at']


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    """Admin for Withdrawal Requests"""
    list_display = [
        'withdrawal_reference',
        'employee_wallet',
        'amount',
        'currency',
        'status',
        'compliance_form_filled',
        'agent_call_scheduled',
        'agent_call_completed',
        'tac_verified_at',
        'created_at'
    ]
    list_filter = ['status', 'compliance_form_filled', 'agent_call_scheduled', 'agent_call_completed']
    search_fields = ['withdrawal_reference', 'employee_wallet__wallet_number', 'bank_account__account_number']
    readonly_fields = ['withdrawal_reference', 'created_at', 'updated_at', 'processed_at']


@admin.register(ActivityFeed)
class ActivityFeedAdmin(admin.ModelAdmin):
    list_display = ['user', 'activity_type', 'display_text', 'created_at']
    list_filter = ['activity_type', 'created_at']
    search_fields = ['user__email', 'display_text', 'reference']
    readonly_fields = ['created_at']


# REMOVED: ManualPaymentReleaseAdmin and KYCVerificationAdmin
# because those models have been removed