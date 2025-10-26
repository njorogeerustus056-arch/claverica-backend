from django.contrib import admin
from .models import Escrow

@admin.register(Escrow)
class EscrowAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'amount', 'is_released', 'created_at')
    search_fields = ('sender__username', 'receiver__username')
    list_filter = ('is_released',)
