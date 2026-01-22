from django.contrib import admin
from .models import Payment, PaymentMethod

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'amount', 'status', 'user', 'created_at']
    search_fields = ['amount', 'status', 'user__email']
    list_filter = ['status', 'created_at']

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['id', 'display_name', 'method_type', 'user', 'created_at']
    search_fields = ['display_name', 'method_type', 'user__email']
    list_filter = ['method_type', 'created_at']
