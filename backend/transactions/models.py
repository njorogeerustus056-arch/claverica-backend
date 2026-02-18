from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
from accounts.models import Account

class Wallet(models.Model):
    """Main wallet for user funds"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.OneToOneField(
        Account,
        on_delete=models.CASCADE,
        related_name="wallet",
        to_field="account_number",
        db_column="account_number"
    )
    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))]
    )
    currency = models.CharField(max_length=3, default="USD")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "transactions"
        db_table = "wallets"
        verbose_name = "Wallet"
        verbose_name_plural = "Wallets"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Wallet {self.account.account_number} - {self.balance} {self.currency}"

class Bank(models.Model):
    """Supported banks for transfers"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    country = models.CharField(max_length=50)
    transfer_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = "transactions"
        db_table = "banks"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"

class Transaction(models.Model):
    """Audit trail for all money movements"""
    TRANSACTION_TYPES = [
        ('credit', 'Credit (Payment Received)'),    # CHANGED: Was 'payment_in'
        ('debit', 'Debit (Transfer Sent)'),         # CHANGED: Was 'transfer_out'
        ('fee', 'Service Fee'),
        ('refund', 'Refund'),
        # Added types to match services.py usage
        ('payment_in', 'Payment Received'),         # Keep for backward compatibility
        ('transfer_out', 'Transfer Sent'),          # Keep for backward compatibility
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    balance_before = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)
    metadata = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "transactions"
        db_table = "transactions"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['wallet', 'timestamp']),
            models.Index(fields=['reference']),
        ]

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} - {self.timestamp}"

class UserBankAccount(models.Model):
    """User's personal bank accounts for transfers"""
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='bank_accounts',
        to_field='account_number'
    )
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE)
    account_name = models.CharField(max_length=200)
    account_number = models.CharField(max_length=50)
    branch = models.CharField(max_length=100, blank=True)
    is_verified = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "transactions"
        db_table = "user_bank_accounts"
        ordering = ['-created_at']
        unique_together = ['account', 'bank', 'account_number']

    def __str__(self):
        return f"{self.account_name} - {self.bank.name} ({self.account_number})"
