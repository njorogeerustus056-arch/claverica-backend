from django.contrib import admin
from .models import PaymentCard, Payment, PaymentMethod

@admin.register(PaymentCard)
class PaymentCardAdmin(admin.ModelAdmin):
    list_display = ['id', 'last_four', 'brand', 'created_at']
    search_fields = ['last_four', 'brand']
    list_filter = ['brand', 'created_at']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'amount', 'status', 'created_at']
    search_fields = ['amount', 'status']
    list_filter = ['status', 'created_at']

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['id', 'display_name', 'method_type', 'created_at']
    search_fields = ['display_name', 'method_type']
    list_filter = ['method_type', 'created_at']
