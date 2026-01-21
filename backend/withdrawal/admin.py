from django.contrib import admin
from .models import Requests

@admin.register(Requests)
class RequestsAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'amount', 'currency', 'status', 'destination_type', 'requires_tac')
    list_filter = ('status', 'currency', 'destination_type', 'requires_tac')
    search_fields = ('user_id', 'transaction_hash', 'notes', 'rejection_reason')
    readonly_fields = ('id',)
    
    fieldsets = (
        ('Request Details', {
            'fields': ('user_id', 'amount', 'currency', 'destination_type', 'destination_details')
        }),
        ('Status & Processing', {
            'fields': ('status', 'requires_tac', 'tac_verified', 'tac_code_id', 'compliance_status', 'kyc_status')
        }),
        ('Processing Information', {
            'fields': ('processed_by', 'processed_at', 'transaction_hash', 'completed_at')
        }),
        ('Notes & Reasons', {
            'fields': ('notes', 'rejection_reason', 'name')
        }),
    )
    
    actions = ['mark_as_approved', 'mark_as_rejected']
    
    def mark_as_approved(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} withdrawal requests marked as approved.')
    mark_as_approved.short_description = 'Mark selected as approved'
    
    def mark_as_rejected(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} withdrawal requests marked as rejected.')
    mark_as_rejected.short_description = 'Mark selected as rejected'
