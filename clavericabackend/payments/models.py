from django.db import models
from django.conf import settings  # CHANGED: Import settings instead of User
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid

class Account(models.Model):
    """User's main account with balance tracking"""
    ACCOUNT_TYPES = [
        ('checking', 'Checking Account'),
        ('savings', 'Savings Account'),
        ('business', 'Business Account'),
    ]

    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
        ('KES', 'Kenyan Shilling'),
        ('NGN', 'Nigerian Naira'),
        ('ZAR', 'South African Rand'),
        ('BTC', 'Bitcoin'),
        ('ETH', 'Ethereum'),
    ]

    # CHANGED: User to settings.AUTH_USER_MODEL
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='accounts')
    account_number = models.CharField(max_length=20, unique=True, editable=False)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='checking')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    balance = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    available_balance = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        # CHANGED: Access email instead of username since your Account model uses email
        return f"{self.user.email} - {self.account_number} ({self.currency})"

    def save(self, *args, **kwargs):
        if not self.account_number:
            # Generate unique account number
            self.account_number = f"CLV{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']


class Transaction(models.Model):
    """All transactions including transfers, deposits, withdrawals"""
    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('transfer', 'Transfer'),
        ('payment', 'Payment'),
        ('refund', 'Refund'),
        ('crypto_buy', 'Crypto Purchase'),
        ('crypto_sell', 'Crypto Sale'),
        ('investment', 'Investment'),
        ('loan_disbursement', 'Loan Disbursement'),
        ('loan_repayment', 'Loan Repayment'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('reversed', 'Reversed'),
    ]

    # Removed any potential UUID PK override - use default BigAutoField
    # No custom id field here

    transaction_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # For transfers
    recipient_account = models.ForeignKey(
        Account, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='received_transactions'
    )
    recipient_name = models.CharField(max_length=255, blank=True)
    recipient_email = models.EmailField(blank=True)

    # Additional details
    description = models.TextField(blank=True)
    reference_number = models.CharField(max_length=100, blank=True)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    # Exchange rate for currency conversions
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.transaction_id} - {self.transaction_type} - {self.amount} {self.currency}"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['transaction_type']),
        ]


class Card(models.Model):
    """Virtual and physical cards"""
    CARD_TYPES = [
        ('virtual', 'Virtual Card'),
        ('physical', 'Physical Card'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('blocked', 'Blocked'),
        ('expired', 'Expired'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='cards')
    card_number = models.CharField(max_length=16, unique=True)
    card_type = models.CharField(max_length=10, choices=CARD_TYPES)
    cardholder_name = models.CharField(max_length=255)
    expiry_month = models.IntegerField()
    expiry_year = models.IntegerField()
    cvv = models.CharField(max_length=4)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    spending_limit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.card_type} - {self.card_number[-4:]} - {self.cardholder_name}"

    class Meta:
        ordering = ['-created_at']


class Beneficiary(models.Model):
    """Saved beneficiaries for quick transfers"""
    # CHANGED: User to settings.AUTH_USER_MODEL
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='beneficiaries')
    name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50)
    bank_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='Kenya')
    currency = models.CharField(max_length=3, default='USD')
    is_favorite = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.account_number}"

    class Meta:
        verbose_name_plural = 'Beneficiaries'
        ordering = ['-is_favorite', 'name']


class SavingsGoal(models.Model):
    """Savings vaults/goals"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='savings_goals')
    name = models.CharField(max_length=255)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=3, default='USD')
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('5.20'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    target_date = models.DateField(null=True, blank=True)
    auto_deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    auto_deposit_frequency = models.CharField(
        max_length=20, 
        choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')],
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.current_amount}/{self.target_amount}"

    @property
    def progress_percentage(self):
        if self.target_amount > 0:
            return (self.current_amount / self.target_amount) * 100
        return 0

    class Meta:
        ordering = ['-created_at']


class CryptoWallet(models.Model):
    """Crypto wallet for each supported cryptocurrency"""
    CRYPTO_TYPES = [
        ('BTC', 'Bitcoin'),
        ('ETH', 'Ethereum'),
        ('USDT', 'Tether'),
        ('BNB', 'Binance Coin'),
        ('SOL', 'Solana'),
        ('XRP', 'Ripple'),
        ('DOGE', 'Dogecoin'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='crypto_wallets')
    crypto_type = models.CharField(max_length=10, choices=CRYPTO_TYPES)
    wallet_address = models.CharField(max_length=255, unique=True)
    balance = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.00000000'))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.crypto_type} - {self.balance}"

    class Meta:
        ordering = ['crypto_type']
        unique_together = ['account', 'crypto_type']


class Subscription(models.Model):
    """Track user subscriptions"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('paused', 'Paused'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='subscriptions')
    service_name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    billing_cycle = models.CharField(
        max_length=20,
        choices=[('monthly', 'Monthly'), ('yearly', 'Yearly'), ('weekly', 'Weekly')],
        default='monthly'
    )
    next_billing_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    merchant_name = models.CharField(max_length=255, blank=True)
    category = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.service_name} - {self.amount} {self.currency}/{self.billing_cycle}"

    class Meta:
        ordering = ['next_billing_date']


class Payment(models.Model):
    """Legacy payment model - kept for backwards compatibility"""
    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
    ]
    # CHANGED: User to settings.AUTH_USER_MODEL
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='pending')

    def __str__(self):
        # CHANGED: Access email instead of username
        return f"{self.user.email} - {self.transaction_type} - {self.amount}"