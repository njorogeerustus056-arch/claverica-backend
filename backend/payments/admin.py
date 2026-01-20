
from django.contrib import admin
from .models import Card, Payment, Transaction

class SafeCardAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'card_type']
    def get_queryset(self, request):
        try:
            return super().get_queryset(request)
        except:
            return Card.objects.none()

class SafePaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'amount']
    def get_queryset(self, request):
        try:
            return super().get_queryset(request)
        except:
            return Payment.objects.none()

class SafeTransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'amount']
    def get_queryset(self, request):
        try:
            return super().get_queryset(request)
        except:
            return Transaction.objects.none()

admin.site.register(Card, SafeCardAdmin)
admin.site.register(Payment, SafePaymentAdmin)
admin.site.register(Transaction, SafeTransactionAdmin)
