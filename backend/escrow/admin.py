from django.contrib import admin
from .models import Escrow

@admin.register(Escrow)
class EscrowAdmin(admin.ModelAdmin):
    list_display = ['name', 'amount', 'currency', 'status', 'created_at']
    list_filter = ['status', 'currency']
    search_fields = ['name', 'escrow_id']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'amount', 'currency', 'status')
        }),
        ('Parties', {
            'fields': ('sender_name', 'receiver_name'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
