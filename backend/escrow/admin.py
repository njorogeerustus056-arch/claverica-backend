# escrow/admin.py - UPDATED FOR COMPLIANCE INTEGRATION

from django.contrib import admin
from .models import Escrow, EscrowLog

@admin.register(Escrow)
class EscrowAdmin(admin.ModelAdmin):
    list_display = [
        'escrow_id', 'sender_name', 'receiver_name', 'amount',
        'currency', 'status', 'is_released', 'requires_compliance_approval',  # NEW
        'compliance_reference',  # NEW
        'created_at'
    ]
    list_filter = [
        'status', 'is_released', 'dispute_status', 
        'requires_compliance_approval',  # NEW
        'created_at'
    ]
    search_fields = [
        'escrow_id', 'sender_name', 'receiver_name', 
        'title', 'description', 'compliance_reference'  # NEW
    ]
    readonly_fields = [
        'id', 'escrow_id', 'total_amount', 'created_at',
        'updated_at', 'funded_at', 'released_at',
        'compliance_reference'  # NEW
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
        ('Compliance', {  # NEW: Compliance section
            'fields': ('compliance_reference', 'requires_compliance_approval'),
            'classes': ('collapse',)
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