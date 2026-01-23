from django.contrib import admin
from .models import Card

@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('card_type', 'last_four', 'user', 'status', 'balance', 'is_primary')
    list_filter = ('card_type', 'status', 'is_primary')
    search_fields = ('card_number', 'last_four', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Card Information', {
            'fields': ('user', 'card_type', 'last_four', 'cvv', 'expiry_date', 'cardholder_name')
        }),
        ('Financial Information', {
            'fields': ('balance', 'spending_limit')
        }),
        ('Status & Appearance', {
            'fields': ('status', 'color_scheme', 'is_primary')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
