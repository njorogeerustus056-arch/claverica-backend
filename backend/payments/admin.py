from django.contrib import admin
from .models import Card, Payment, Transaction, PaymentMethod

class CardAdmin(admin.ModelAdmin):
    list_display = ['id', 'last4', 'brand', 'created_at']
    
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'amount', 'status', 'created_at']
    
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'type', 'amount', 'created_at']
    
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['id', 'display_name', 'method_type', 'created_at']

admin.site.register(Card, CardAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(PaymentMethod, PaymentMethodAdmin)
