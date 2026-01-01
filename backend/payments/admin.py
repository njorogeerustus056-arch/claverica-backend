# payments/admin.py - CORRECTED VERSION

from django.contrib import admin
from .models import Account, Transaction, Card, PaymentMethod, AuditLog


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('account_number', 'user', 'account_type', 'balance', 'available_balance', 'currency', 'is_active')
    list_filter = ('account_type', 'currency', 'is_active', 'created_at')
    search_fields = ('account_number', 'user__username', 'user__email')
    readonly_fields = ('account_number', 'created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'account_number', 'account_type', 'currency', 'is_active')
        }),
        ('Balance Information', {
            'fields': ('balance', 'available_balance')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'account', 'transaction_type', 'amount', 'currency', 'status', 'created_at')
    list_filter = ('transaction_type', 'status', 'currency', 'created_at')
    search_fields = ('transaction_id', 'account__account_number', 'description', 'recipient_name')
    readonly_fields = ('transaction_id', 'created_at', 'updated_at', 'completed_at')
    fieldsets = (
        ('Transaction Details', {
            'fields': ('transaction_id', 'account', 'transaction_type', 'amount', 'currency', 'description')
        }),
        ('Transfer Details', {
            'fields': ('recipient_account', 'recipient_name'),
            'classes': ('collapse',)
        }),
        ('Status Information', {
            'fields': ('status', 'metadata', 'idempotency_key')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at')
        }),
    )


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('last_four', 'account', 'card_type', 'card_network', 'expiry_month', 'expiry_year', 'status', 'is_default')
    list_filter = ('card_type', 'card_network', 'status', 'is_default')
    search_fields = ('last_four', 'account__account_number', 'card_holder_name', 'token')
    readonly_fields = ('token', 'created_at', 'updated_at')
    fieldsets = (
        ('Card Information', {
            'fields': ('account', 'card_type', 'card_network', 'last_four', 'expiry_month', 'expiry_year', 'card_holder_name')
        }),
        ('Security Information', {
            'fields': ('token', 'cvv', 'encrypted_data'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status', 'is_default')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'user', 'method_type', 'is_default')
    list_filter = ('method_type', 'is_default')
    search_fields = ('display_name', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'method_type', 'display_name', 'is_default')
        }),
        ('Linked Payment Methods', {
            'fields': ('card', 'bank_account'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'model_name', 'object_id', 'created_at')
    list_filter = ('action', 'model_name', 'created_at')
    search_fields = ('user__username', 'model_name', 'object_id', 'details')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Audit Information', {
            'fields': ('user', 'action', 'model_name', 'object_id')
        }),
        ('Details', {
            'fields': ('details', 'ip_address', 'user_agent')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )