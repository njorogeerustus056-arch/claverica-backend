"""
Django admin configuration for Cards app
"""

from django.contrib import admin
from .models import Card, CardTransaction


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'card_type', 'last_four', 'cardholder_name',
        'balance', 'spending_limit', 'status', 'is_primary', 'created_at'
    ]
    list_filter = ['card_type', 'status', 'is_primary', 'created_at']
    search_fields = ['user__username', 'card_number', 'last_four', 'cardholder_name']
    readonly_fields = ['card_number', 'last_four', 'cvv', 'expiry_date', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Card Information', {
            'fields': ('user', 'card_type', 'cardholder_name', 'is_primary')
        }),
        ('Card Details', {
            'fields': ('card_number', 'last_four', 'cvv', 'expiry_date', 'color_scheme')
        }),
        ('Financial Details', {
            'fields': ('balance', 'spending_limit', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CardTransaction)
class CardTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'card', 'amount', 'merchant',
        'transaction_type', 'status', 'created_at'
    ]
    list_filter = ['transaction_type', 'status', 'category', 'created_at']
    search_fields = ['user__username', 'merchant', 'description']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('user', 'card', 'amount', 'merchant', 'category')
        }),
        ('Details', {
            'fields': ('transaction_type', 'status', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
