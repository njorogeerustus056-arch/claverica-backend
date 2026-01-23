from django.contrib import admin
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'transaction_type', 'amount', 'created_at']
    list_filter = ['transaction_type']
    search_fields = ['user__email', 'reference']
