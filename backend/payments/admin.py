# payments/admin.py
from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from .models import Payment, PaymentCode
from transactions.models import Wallet, Transaction

# Register your models here

@admin.register(PaymentCode)
class PaymentCodeAdmin(admin.ModelAdmin):
    """Admin interface for Payment Codes"""
    list_display = ('code', 'account_display', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('code', 'account__account_number', 'account__email')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 20

    def account_display(self, obj):
        """Display account with link"""
        return format_html(
            '<a href="/admin/accounts/account/{}/change/">{}</a> - {}',
            obj.account.id,
            obj.account.account_number,
            obj.account.email
        )
    account_display.short_description = 'Account'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin interface for Payments"""
    list_display = ('reference', 'account_display', 'formatted_amount',
                    'sender', 'status', 'admin_user_display', 'created_at', 'balance_before', 'balance_after')
    list_filter = ('status', 'created_at', 'admin_user')
    search_fields = ('reference', 'account__account_number',
                     'account__email', 'sender', 'admin_user__username')
    readonly_fields = ('created_at', 'processed_at', 'reference', 'metadata')
    list_per_page = 20
    fieldsets = (
        ('Payment Information', {
            'fields': ('reference', 'account', 'payment_code', 'amount', 'sender', 'admin_user')
        }),
        ('Status & Tracking', {
            'fields': ('status', 'balance_before', 'balance_after')
        }),
        ('Additional Information', {
            'fields': ('description', 'metadata')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'processed_at'),
            'classes': ('collapse',)
        }),
    )

    def account_display(self, obj):
        """Display account with link"""
        return format_html(
            '<a href="/admin/accounts/account/{}/change/">{}</a> - {}',
            obj.account.id,
            obj.account.account_number,
            obj.account.email
        )
    account_display.short_description = 'Account'

    def admin_user_display(self, obj):
        """Display admin user with link"""
        if obj.admin_user:
            return format_html(
                '<a href="/admin/auth/user/{}/change/">{}</a>',
                obj.admin_user.id,
                obj.admin_user.username
            )
        return "System"
    admin_user_display.short_description = 'Processed By'

    def formatted_amount(self, obj):
        """Format amount with CLV symbol"""
        return f"${obj.amount:,.2f}"
    formatted_amount.short_description = 'Amount'

    # Optional: Add custom actions
    actions = ['mark_as_completed', 'mark_as_failed']

    def mark_as_completed(self, request, queryset):
        """Mark selected payments as completed"""
        from transactions.models import Wallet, Transaction

        for payment in queryset.filter(status__in=['pending', 'failed']):
            try:
                # Update wallet
                wallet, created = Wallet.objects.get_or_create(
                    account=payment.account,
                    defaults={'balance': 0.00, 'currency': 'USD'}
                )

                old_balance = wallet.balance
                wallet.balance += payment.amount
                wallet.save()

                # Update payment balances
                payment.balance_before = old_balance
                payment.balance_after = wallet.balance
                payment.status = 'completed'
                payment.save()

                # Create transaction if doesn't exist
                Transaction.objects.get_or_create(
                    reference=payment.reference,
                    defaults={
                        'account': payment.account,
                        'wallet': wallet,
                        'transaction_type': 'credit',
                        'amount': payment.amount,
                        'description': f'Payment from {payment.sender}',
                        'status': 'completed',
                        'metadata': {'payment_id': payment.id}
                    }
                )

            except Exception as e:
                self.message_user(request, f"Error updating payment {payment.reference}: {e}", messages.ERROR)
                continue

        updated = queryset.update(status='completed')
        self.message_user(request, f"{updated} payment(s) marked as completed and wallets updated.", messages.SUCCESS)
    mark_as_completed.short_description = "Mark selected payments as completed"

    def mark_as_failed(self, request, queryset):
        """Mark selected payments as failed"""
        updated = queryset.update(status='failed')
        self.message_user(request, f"{updated} payment(s) marked as failed.", messages.SUCCESS)
    mark_as_failed.short_description = "Mark selected payments as failed"

    def save_model(self, request, obj, form, change):
        """Custom save to ensure wallet update and track admin"""
        # Set the admin user who processed this payment
        obj.admin_user = request.user
        
        super().save_model(request, obj, form, change)

        # If status changed to completed, trigger wallet update
        if obj.status == 'completed':
            try:
                # Force save to trigger wallet update
                obj.save()
                messages.success(request, f" Payment processed! Wallet updated.")
            except Exception as e:
                messages.warning(request, f" Payment saved but wallet update may have failed: {e}")