from django.contrib import admin
from .models import Transfer, TAC, TransferLog, TransferLimit

@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ['reference', 'account', 'amount', 'status']

@admin.register(TAC)
class TACAdmin(admin.ModelAdmin):
    list_display = ['code', 'transfer', 'status']

@admin.register(TransferLog)
class TransferLogAdmin(admin.ModelAdmin):
    list_display = ['transfer', 'log_type', 'created_at']

@admin.register(TransferLimit)
class TransferLimitAdmin(admin.ModelAdmin):
    list_display = ['limit_type', 'amount', 'is_active']
