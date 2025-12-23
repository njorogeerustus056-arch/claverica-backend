from django.contrib import admin
from .models import Receipt

@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Receipt model.
    Provides list view, filters, search, and organized fieldsets.
    """

    # Columns displayed in the list view
    list_display = [
        'original_file_name',
        'user_id',
        'merchant_name',
        'amount',
        'category',
        'status',
        'uploaded_at'
    ]

    # Filters for quick navigation in the list view
    list_filter = ['status', 'category', 'uploaded_at']

    # Fields searchable via the admin search bar
    search_fields = ['user_id', 'original_file_name', 'merchant_name']

    # Fields that should not be editable in the admin
    readonly_fields = ['id', 'uploaded_at', 'updated_at']

    # Enables date hierarchy navigation
    date_hierarchy = 'uploaded_at'

    # Organize form layout into sections
    fieldsets = (
        ('File Information', {
            'fields': (
                'id',
                'user_id',
                'file_name',
                'original_file_name',
                'file_size',
                'file_type',
                'storage_path'
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
