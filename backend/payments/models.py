"""
payments/models.py - Payment system for admin to credit accounts
"""
from django.db import models
from django.conf import settings
from decimal import Decimal
import uuid


class PaymentCode(models.Model):
    """
    Custom payment codes that admin assigns to accounts
    Example: UASIP57EEO links to a specific CLV account
    """
    account = models.OneToOneField(
        'accounts.Account',
        on_delete=models.CASCADE,
        related_name='payment_code',
        help_text="Account that this payment code belongs to"
    )

    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Custom payment code like UASIP57EEO"
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Can this payment code receive payments?"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Payment Code"
        verbose_name_plural = "Payment Codes"

    def __str__(self):
        return f"{self.code}  {self.account.account_number}"


class Payment(models.Model):
    """
    Records each payment (credit) made by admin to an account
    """
    account = models.ForeignKey(
        'accounts.Account',
        on_delete=models.CASCADE,
        related_name='payments',
        help_text="Account that received the payment"
    )

    payment_code = models.ForeignKey(
        PaymentCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        help_text="Payment code used for this payment"
    )

    # ADD THIS FIELD - It was missing
    admin_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_payments',
        help_text="Admin user who processed this payment"
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Amount credited to account"
    )

    sender = models.CharField(
        max_length=255,
        help_text="Sender name (e.g., 'ecovera')"
    )

    reference = models.CharField(
        max_length=100,
        unique=True,
        help_text="Auto-generated reference like PAY-20260129-001"
    )

    description = models.TextField(
        blank=True,
        help_text="Additional notes about this payment"
    )

    # Status tracking
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='completed',
        help_text="Payment status"
    )

    # Balance tracking
    balance_before = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Account balance before payment"
    )

    balance_after = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Account balance after payment"
    )

    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional data about the payment"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        indexes = [
            models.Index(fields=['account', 'created_at']),
            models.Index(fields=['reference']),
            models.Index(fields=['payment_code']),
            models.Index(fields=['admin_user']),  # Add index for admin_user
        ]

    def __str__(self):
        return f"Payment #{self.reference}: ${self.amount} to {self.account.account_number}"

    def save(self, *args, **kwargs):
        """
        Save payment with auto-generated reference
        WALLET UPDATES ARE HANDLED BY TransactionService in services.py
        """
        # Generate reference if not set
        if not self.reference:
            from django.utils import timezone
            date_str = timezone.now().strftime('%Y%m%d')
            last_payment = Payment.objects.filter(
                reference__startswith=f'PAY-{date_str}'
            ).order_by('-id').first()

            if last_payment:
                try:
                    last_num = int(last_payment.reference.split('-')[-1])
                    new_num = last_num + 1
                except:
                    new_num = 1
            else:
                new_num = 1

            self.reference = f'PAY-{date_str}-{new_num:03d}'

        # Save the payment (wallet updates handled separately by services.py)
        super().save(*args, **kwargs)

    @property
    def formatted_amount(self):
        """Format amount with currency symbol"""
        return f"${self.amount:,.2f}"

    @property
    def account_number(self):
        """Get account number for easy access"""
        return self.account.account_number

    @property
    def account_email(self):
        """Get account email for notifications"""
        return self.account.email