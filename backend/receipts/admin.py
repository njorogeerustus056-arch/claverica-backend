from django.contrib import admin
from .models import Receipt

@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_user_email', 'amount', 'currency', 'status', 'transaction_id')
    list_filter = ('status', 'currency')
    search_fields = ('user__email', 'transaction_id', 'reference')
    readonly_fields = ('id',)
    
    def get_user_email(self, obj):
        return obj.user.email if obj.user else 'No user'
    get_user_email.short_description = 'User Email'
    get_user_email.admin_order_field = 'user__email'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'amount', 'currency', 'status')
        }),
        ('Transaction Details', {
            'fields': ('transaction_id', 'reference', 'payment_method', 'payment_details')
        }),
    )
