from django.contrib import admin
from .models import Receipt

@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'currency', 'status', 'transaction_id')
    list_filter = ('status', 'currency')
    search_fields = ('user__email', 'transaction_id')
    readonly_fields = ('created_at',)
