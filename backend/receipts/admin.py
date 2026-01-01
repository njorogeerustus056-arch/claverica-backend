from django.contrib import admin
from .models import Receipt

@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Receipt model.
    """
    list_display = [
        'original_file_name',
        'user',
        'merchant_name',
        'amount',
        'category',
        'status',
        'uploaded_at'
    ]

    list_filter = ['status', 'category', 'uploaded_at']
    search_fields = ['user__email', 'original_file_name', 'merchant_name']
    readonly_fields = ['id', 'uploaded_at', 'updated_at', 'file_size_mb']
    date_hierarchy = 'uploaded_at'

    fieldsets = (
        ('File Information', {
            'fields': (
                'id',
                'user',
                'file',
                'original_file_name',
                'file_size',
                'file_type',
            )
        }),
        ('Receipt Details', {
            'fields': (
                'merchant_name',
                'amount',
                'currency',
                'transaction_date',
                'category',
                'notes',
                'tags'
            )
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('uploaded_at', 'updated_at')
        }),
    )
    
    def file_size_mb(self, obj):
        return f"{obj.file_size_mb} MB"
    file_size_mb.short_description = "File Size (MB)"