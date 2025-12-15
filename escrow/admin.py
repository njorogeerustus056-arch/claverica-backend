from django.contrib import admin
from .models import Escrow, EscrowMessage, EscrowLog

@admin.register(Escrow)
class EscrowAdmin(admin.ModelAdmin):
    list_display = ['escrow_id', 'sender_name', 'receiver_name', 'amount', 
                    'currency', 'status', 'is_released', 'created_at']
    list_filter = ['status', 'is_released', 'dispute_status', 'created_at']
    search_fields = ['escrow_id', 'sender_name', 'receiver_name', 'title', 'description']
    readonly_fields = ['id', 'escrow_id', 'total_amount', 'created_at', 'updated_at', 
                      'funded_at', 'released_at']
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
            'fields': ('status', 'is_released', 'release_approved_by_sender', 
                      'release_approved_by_receiver', 'expected_release_date')
        }),
        ('Dispute Information', {
            'fields': ('dispute_status', 'dispute_reason', 'dispute_opened_by', 
                      'dispute_opened_at'),
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


@admin.register(EscrowMessage)
class EscrowMessageAdmin(admin.ModelAdmin):
    list_display = ['escrow', 'sender_name', 'message', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['escrow__escrow_id', 'sender_name', 'message']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'created_at'


@admin.register(EscrowLog)
class EscrowLogAdmin(admin.ModelAdmin):
    list_display = ['escrow', 'user_name', 'action', 'timestamp', 'ip_address']
    list_filter = ['action', 'timestamp']
    search_fields = ['escrow__escrow_id', 'user_name', 'details']
    readonly_fields = ['id', 'timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Log Information', {
            'fields': ('id', 'escrow', 'user_id', 'user_name', 'action')
        }),
        ('Details', {
            'fields': ('details', 'ip_address')
        }),
        ('Timestamp', {
            'fields': ('timestamp',)
        }),
    )
