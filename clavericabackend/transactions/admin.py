from django.contrib import admin
from .models import Transaction, TransactionLog

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'user_id', 'type', 'amount', 'currency', 
                    'merchant', 'category', 'status', 'transaction_date']
    list_filter = ['status', 'type', 'category', 'transaction_date']
    search_fields = ['transaction_id', 'user_id', 'merchant', 'description']
    readonly_fields = ['id', 'transaction_id', 'created_at', 'updated_at']
    date_hierarchy = 'transaction_date'
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('id', 'transaction_id', 'user_id', 'type', 'status')
        }),
        ('Amount Details', {
            'fields': ('amount', 'currency', 'merchant', 'category')
        }),
        ('Additional Information', {
            'fields': ('description', 'reference', 'account_number')
        }),
        ('Timestamps', {
            'fields': ('transaction_date', 'created_at', 'updated_at')
        }),
    )


@admin.register(TransactionLog)
class TransactionLogAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'action', 'transaction', 'timestamp', 'ip_address']
    list_filter = ['action', 'timestamp']
    search_fields = ['user_id', 'action', 'details']
    readonly_fields = ['id', 'timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Log Information', {
            'fields': ('id', 'user_id', 'transaction', 'action')
        }),
        ('Details', {
            'fields': ('details', 'ip_address', 'user_agent')
        }),
        ('Timestamp', {
            'fields': ('timestamp',)
        }),
    )
