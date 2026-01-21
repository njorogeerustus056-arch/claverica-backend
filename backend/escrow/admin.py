from django.contrib import admin
from .models import Escrow, Escrowlog

@admin.register(Escrow)
class EscrowAdmin(admin.ModelAdmin):
    list_display = ('escrow_id', 'title', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('escrow_id', 'title')
    readonly_fields = ('created_at',)

@admin.register(Escrowlog)
class EscrowlogAdmin(admin.ModelAdmin):
    list_display = ('escrow', 'action', 'created_at')
    list_filter = ('action', 'created_at')
