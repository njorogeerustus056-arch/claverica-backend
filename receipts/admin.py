from django.contrib import admin
from .models import Receipt

@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ['original_file_name', 'user_id', 'merchant_name', 'amount', 
                    'category', 'status', 'uploaded_at']
    list_filter = ['status', 'category', 'uploaded_at']
    search_fields = ['user_id', 'original_file_name', 'merchant_name']
    readonly_fields = ['id', 'uploaded_at', 'updated_at']
    date_hierarchy = 'uploaded_at'
    
    fieldsets = (
        ('File Information', {
            'fields': ('id', 'user_id', 'file_name', 'original_file_name', 
                      'file_size', 'file_type', 'storage_path')
        }),
        ('Receipt Details', {
            'fields': ('merchant_name', 'amount', 'currency', 'transaction_date', 
                      'category', 'notes', 'tags')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('uploaded_at', 'updated_at')
        }),
    )
