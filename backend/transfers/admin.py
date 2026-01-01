from django.contrib import admin
from .models import Recipient, Transfer, TransferLog, TACCode

@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = ['name', 'recipient_type', 'country', 'user', 'is_favorite', 'is_verified', 'created_at']
    list_filter = ['recipient_type', 'is_favorite', 'is_verified', 'country']
    search_fields = ['name', 'country', 'account_number', 'wallet_address', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'recipient_type', 'name', 'country', 'logo')
        }),
        ('Bank/Fintech Details', {
            'fields': ('account_number', 'account_holder', 'swift_code', 'iban', 'routing_number', 'bank_name'),
            'classes': ('collapse',)
        }),
        ('Crypto Details', {
            'fields': ('wallet_address', 'network'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_favorite', 'is_verified')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class TransferLogInline(admin.TabularInline):
    model = TransferLog
    extra = 0
    readonly_fields = ['status', 'message', 'created_by', 'created_at']
    can_delete = False


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ['transfer_id', 'sender', 'recipient_name', 'amount', 'currency', 'status', 'transfer_type', 'created_at']
    list_filter = ['status', 'transfer_type', 'currency', 'requires_tac', 'tac_verified']
    search_fields = ['transfer_id', 'sender__username', 'recipient_name', 'reference_number']
    readonly_fields = ['transfer_id', 'total_amount', 'created_at', 'updated_at', 'completed_at']
    inlines = [TransferLogInline]
    
    fieldsets = (
        ('Transfer Information', {
            'fields': ('transfer_id', 'sender', 'recipient', 'transfer_type')
        }),
        ('Amount Details', {
            'fields': ('amount', 'currency', 'fee', 'total_amount')
        }),
        ('Recipient Details', {
            'fields': ('recipient_name', 'recipient_account', 'recipient_bank'),
            'classes': ('collapse',)
        }),
        ('Status & Tracking', {
            'fields': ('status', 'description', 'reference_number')
        }),
        ('Compliance', {
            'fields': ('requires_tac', 'tac_verified', 'tac_verified_at', 'compliance_status', 'compliance_notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_completed', 'mark_as_failed', 'mark_as_cancelled']
    
    def mark_as_completed(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='completed', completed_at=timezone.now())
        self.message_user(request, f'{updated} transfer(s) marked as completed.')
    mark_as_completed.short_description = "Mark selected transfers as completed"
    
    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} transfer(s) marked as failed.')
    mark_as_failed.short_description = "Mark selected transfers as failed"
    
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} transfer(s) marked as cancelled.')
    mark_as_cancelled.short_description = "Mark selected transfers as cancelled"


@admin.register(TransferLog)
class TransferLogAdmin(admin.ModelAdmin):
    list_display = ['transfer', 'status', 'created_at', 'created_by']
    list_filter = ['status', 'created_at']
    search_fields = ['transfer__transfer_id', 'message']
    readonly_fields = ['transfer', 'status', 'message', 'created_by', 'created_at']


@admin.register(TACCode)
class TACCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'user', 'transfer', 'is_used', 'expires_at', 'created_at']
    list_filter = ['is_used', 'created_at', 'expires_at']
    search_fields = ['code', 'user__username', 'transfer__transfer_id']
    readonly_fields = ['created_at', 'used_at']
    
    fieldsets = (
        ('TAC Information', {
            'fields': ('user', 'transfer', 'code')
        }),
        ('Status', {
            'fields': ('is_used', 'used_at', 'expires_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
