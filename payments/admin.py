from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'transaction_type', 'status', 'timestamp')
    search_fields = ('user__username',)
    list_filter = ('transaction_type', 'status')
