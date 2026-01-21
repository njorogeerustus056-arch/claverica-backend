from django.contrib import admin
from .models import Escrow, EscrowLog

@admin.register(Escrow)
class EscrowAdmin(admin.ModelAdmin):
    # Show important fields in list view
    list_display = ['title', 'amount', 'currency', 'status', 'is_released', 'created_at']
    
    # Simple form with just the essential fields (like your screenshot)
    fields = ['title', 'description', 'amount', 'currency', 'status']
    
    # Filters and search
    list_filter = ['status', 'currency', 'is_released']
    search_fields = ['title', 'escrow_id', 'sender_name', 'receiver_name']
    
    # Read-only fields
    readonly_fields = ['created_at', 'updated_at']

@admin.register(EscrowLog)
class EscrowLogAdmin(admin.ModelAdmin):
    list_display = ['escrow', 'action', 'created_at']
    list_filter = ['action']
    search_fields = ['escrow__title', 'details']
    readonly_fields = ['created_at']
