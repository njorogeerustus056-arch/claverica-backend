from django.contrib import admin
from .models import Escrow  # Only import Escrow

@admin.register(Escrow)
class EscrowAdmin(admin.ModelAdmin):
    list_display = [
        'escrow_id', 'sender_name', 'receiver_name', 'amount',
        'currency', 'status', 'is_released', 'created_at'
    ]
    list_filter = ['status', 'is_released', 'dispute_status', 'created_at']
    search_fields = ['escrow_id', 'sender_name', 'receiver_name', 'title', 'description']
    readonly_fields = [
        'id', 'escrow_id', 'total_amount', 'created_at',
        'updated_at', 'funded_at', 'released_at'
    ]
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Escrow Information', {
            'fields': ('id', 'escrow_id', 'title', 'description', 'terms_and_conditions')
        }),
        ('Parties Involved', {
            'fields': ('sender_id', 'sender_name', 'receiver_id', 'receiver_name')
        }),
        ('Financial Details', {
            'fields': ('amount', 'currency', 'fee', 'total_amount')
        }),
        ('Status & Release', {
            'fields': (
                'status', 'is_released',
                'release_approved_by_sender',
                'release_approved_by_receiver',
                'expected_release_date'
            )
        }),
        ('Dispute Information', {
            'fields': (
                'dispute_status', 'dispute_reason',
                'dispute_opened_by', 'dispute_opened_at'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'funded_at', 'released_at')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )
