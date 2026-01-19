from django.contrib import admin
from .models import TransferRequest

@admin.register(TransferRequest)
class TransferRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'sender', 'amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
