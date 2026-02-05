"""
cards/admin.py - Card admin interface
"""
from django.contrib import admin
from .models import Card


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    """Admin interface for Cards"""
    
    list_display = [
        'id', 
        'account',           # Shows Account __str__
        'masked_number',     # Shows **** **** **** 1234
        'display_name',      # Shows user name
        'balance',           # Computed from Wallet
        'status', 
        'is_primary'
    ]
    
    list_filter = ['status', 'is_primary', 'card_type']
    
    search_fields = [
        'card_number',
        'last_four',
        'account__account_number',
        'account__user__email',
        'account__user__first_name',
        'account__user__last_name'
    ]
    
    readonly_fields = [
        'balance',
        'account_number',
        'full_name',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Card Information', {
            'fields': (
                'account',
                'card_type',
                'card_number',
                'last_four',
                'expiry_date',
                'cardholder_name',
            )
        }),
        ('Status & Display', {
            'fields': ('status', 'color_scheme', 'is_primary')
        }),
        ('Computed Information (Read-only)', {
            'fields': ('balance', 'account_number', 'full_name', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
