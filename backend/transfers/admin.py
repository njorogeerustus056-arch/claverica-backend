"""
transfers/admin.py - Updated admin interface
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Transfer, TransferLog, TransferLimit


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    """Admin interface for transfers"""
    
    list_display = [
        'transfer_id', 'user_email', 'amount_currency', 'recipient_name',
        'status_badge', 'risk_level_badge', 'created_at', 'admin_actions'
    ]
    list_filter = ['status', 'risk_level', 'currency', 'created_at']
    search_fields = ['transfer_id', 'user__email', 'recipient_name', 'recipient_account']
    readonly_fields = ['transfer_id', 'created_at', 'updated_at', 'tac_verified_at', 'processed_at', 'completed_at']
    fieldsets = (
        ('Transfer Information', {
            'fields': ('transfer_id', 'user', 'amount', 'currency', 'description')
        }),
        ('Recipient Information', {
            'fields': ('recipient_name', 'recipient_account', 'recipient_bank', 'recipient_country', 'recipient_phone', 'recipient_email')
        }),
        ('Compliance Information', {
            'fields': ('compliance_request', 'risk_level', 'tac_required', 'tac_verified', 'video_call_required', 'video_call_completed')
        }),
        ('Status & Timeline', {
            'fields': ('status', 'priority', 'created_at', 'updated_at', 'submitted_at', 'processed_at', 'completed_at')
        }),
        ('Fees & Charges', {
            'fields': ('fee', 'tax', 'total_amount')
        }),
        ('Additional Information', {
            'fields': ('reference', 'notes', 'ip_address', 'user_agent', 'device_id')
        }),
    )
    actions = ['approve_transfers', 'reject_transfers', 'generate_tac', 'mark_as_completed']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    
    def amount_currency(self, obj):
        return f"{obj.amount} {obj.currency}"
    amount_currency.short_description = 'Amount'
    
    def status_badge(self, obj):
        color_map = {
            'draft': 'gray',
            'pending': 'blue',
            'processing': 'orange',
            'completed': 'green',
            'failed': 'red',
            'cancelled': 'gray',
            'compliance_review': 'yellow',
            'awaiting_tac': 'purple',
            'awaiting_video_call': 'teal',
        }
        color = color_map.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 10px; font-size: 12px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def risk_level_badge(self, obj):
        color_map = {
            'low': 'green',
            'medium': 'orange',
            'high': 'red',
        }
        color = color_map.get(obj.risk_level, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 10px; font-size: 12px;">{}</span>',
            color, obj.risk_level.upper()
        )
    risk_level_badge.short_description = 'Risk'
    
    def admin_actions(self, obj):
        return format_html(
            '<a href="/admin/transfers/transfer/{}/change/" class="button">Edit</a>&nbsp;'
            '<a href="/admin/transfers/transfer/{}/history/" class="button">History</a>',
            obj.id, obj.id
        )

    def approve_transfers(self, request, queryset):
        """Approve selected transfers"""
        from .services import TransferComplianceService
        
        for transfer in queryset:
            if transfer.status in ['pending', 'compliance_review']:
                # Update compliance request if exists
                if transfer.compliance_request:
                    transfer.compliance_request.status = 'approved'
                    transfer.compliance_request.save()
                
                transfer.status = 'pending'
                transfer.save()
                
                # Create log
                TransferLog.objects.create(
                    transfer=transfer,
                    log_type='status_change',
                    message='Transfer approved by admin',
                    created_by=request.user,
                    metadata={'new_status': 'pending', 'approved_by': request.user.email}
                )
        
        self.message_user(request, f"{queryset.count()} transfers approved.")
    approve_transfers.short_description = "Approve selected transfers"
    
    def reject_transfers(self, request, queryset):
        """Reject selected transfers"""
        for transfer in queryset:
            if transfer.status in ['pending', 'compliance_review']:
                # Update compliance request if exists
                if transfer.compliance_request:
                    transfer.compliance_request.status = 'rejected'
                    transfer.compliance_request.save()
                
                transfer.status = 'cancelled'
                transfer.save()
                
                # Create log
                TransferLog.objects.create(
                    transfer=transfer,
                    log_type='status_change',
                    message='Transfer rejected by admin',
                    created_by=request.user,
                    metadata={'new_status': 'cancelled', 'rejected_by': request.user.email}
                )
        
        self.message_user(request, f"{queryset.count()} transfers rejected.")
    reject_transfers.short_description = "Reject selected transfers"
    
    def generate_tac(self, request, queryset):
        """Generate TAC for selected transfers"""
        from .services import TransferComplianceService
        
        for transfer in queryset:
            if transfer.tac_required and not transfer.tac_verified:
                try:
                    result = TransferComplianceService.generate_tac_for_transfer(transfer)
                    if result['success']:
                        self.message_user(request, f"TAC generated for {transfer.transfer_id}")
                except Exception as e:
                    self.message_user(request, f"Failed to generate TAC for {transfer.transfer_id}: {str(e)}", level='error')
        
        self.message_user(request, "TAC generation process completed.")
    generate_tac.short_description = "Generate TAC for selected transfers"
    
    def mark_as_completed(self, request, queryset):
        """Mark selected transfers as completed"""
        for transfer in queryset:
            if transfer.status == 'processing':
                transfer.status = 'completed'
                transfer.completed_at = timezone.now()
                transfer.save()
                
                # Create log
                TransferLog.objects.create(
                    transfer=transfer,
                    log_type='status_change',
                    message='Transfer marked as completed by admin',
                    created_by=request.user,
                    metadata={'new_status': 'completed', 'completed_by': request.user.email}
                )
        
        self.message_user(request, f"{queryset.count()} transfers marked as completed.")
    mark_as_completed.short_description = "Mark as completed"


    admin_actions.short_description = 'Actions'
@admin.register(TransferLog)
class TransferLogAdmin(admin.ModelAdmin):
    """Admin interface for transfer logs"""
    
    list_display = ['transfer_id', 'log_type', 'message_short', 'created_by_email', 'created_at']
    list_filter = ['log_type', 'created_at']
    search_fields = ['transfer__transfer_id', 'message', 'created_by__email']
    readonly_fields = ['created_at']
    
    def transfer_id(self, obj):
        return obj.transfer.transfer_id
    transfer_id.short_description = 'Transfer ID'
    
    def created_by_email(self, obj):
        return obj.created_by.email if obj.created_by else 'System'
    created_by_email.short_description = 'Created By'
    
    def message_short(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_short.short_description = 'Message'


@admin.register(TransferLimit)
class TransferLimitAdmin(admin.ModelAdmin):
    """Admin interface for transfer limits"""
    
    list_display = ['user_email', 'country', 'currency', 'limit_type', 'amount', 'is_active']
    list_filter = ['limit_type', 'currency', 'is_active', 'country']
    search_fields = ['user__email', 'country', 'limit_type']
    
    def user_email(self, obj):
        return obj.user.email if obj.user else 'Global'
    user_email.short_description = 'User'