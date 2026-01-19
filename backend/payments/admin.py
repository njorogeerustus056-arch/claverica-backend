from django.contrib import admin
from .models import Account, Card, PaymentMethod, Payment, Transaction

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['account_number', 'user', 'balance', 'currency', 'created_at']

@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ['card_number', 'user', 'card_type', 'expiry_date']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'amount', 'status', 'created_at']

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'account', 'amount', 'transaction_type', 'created_at']
