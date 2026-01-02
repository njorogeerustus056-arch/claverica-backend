# payments/admin.py - UPDATED VERSION
from django.contrib import admin
from .models import Account, Transaction, Card, PaymentMethod, AuditLog


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = [
        'account_number', 
        'user', 
        'account_type', 
        'balance',
        'available_balance',
        'currency', 
        'is_verified',
        'is_active'
    ]
    list_filter = [
        'account_type', 
        'currency', 
        'is_verified',
        'is_active',
        'created_at'
    ]
    search_fields = [
        'account_number', 
        'user__email', 
        'user__first_name', 
        'user__last_name'
    ]
    readonly_fields = ['account_number', 'created_at', 'updated_at']
    list_per_page = 20


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_id',
        'transaction_type',
        'amount',
        'currency',
        'status',
        'created_at',
        'completed_at'
    ]
    list_filter = [
        'transaction_type',
        'status',
        'currency',
        'created_at'
    ]
    search_fields = [
        'transaction_id',
        'account__account_number',
        'recipient_account__account_number',
        'description',
        'recipient_name'
    ]
    readonly_fields = ['transaction_id', 'created_at', 'updated_at', 'completed_at']
    list_per_page = 30


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = [
        'last_four',
        'card_network',
        'card_type',
        'card_holder_name',
        'account',
        'is_default',
        'status',
        'created_at'
    ]
    list_filter = [
        'card_network',
        'card_type',
        'status',
        'is_default',
        'created_at'
    ]
    search_fields = [
        'last_four',
        'card_holder_name',
        'account__account_number',
        'account__user__email'
    ]
    readonly_fields = ['token', 'encrypted_data', 'created_at', 'updated_at']
    list_per_page = 20


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'method_type',
        'display_name',
        'is_default',
        'created_at'
    ]
    list_filter = [
        'method_type',
        'is_default',
        'created_at'
    ]
    search_fields = [
        'user__email',
        'display_name',
        'card__last_four',
        'bank_account__account_number'
    ]
    list_per_page = 20


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'action',
        'model_name',
        'object_id',
        'created_at'
    ]
    list_filter = [
        'action',
        'model_name',
        'created_at'
    ]
    search_fields = [
        'user__email',
        'action',
        'model_name',
        'object_id',
        'details'
    ]
    readonly_fields = ['user', 'action', 'model_name', 'object_id', 'details', 'ip_address', 'user_agent', 'created_at']
    list_per_page = 50