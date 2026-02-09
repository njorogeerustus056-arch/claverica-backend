"""
cards/models.py - Get user name from User model via Account
"""
from django.db import models
from decimal import Decimal


class CardType(models.TextChoices):
    VIRTUAL = 'virtual', 'Virtual'
    PHYSICAL = 'physical', 'Physical'


class CardStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    FROZEN = 'frozen', 'Frozen'
    CANCELLED = 'cancelled', 'Cancelled'


class Card(models.Model):
    """Card that displays Account and Wallet information"""

    # Link to Account (which has ForeignKey to User)
    account = models.ForeignKey(
        'accounts.Account',
        on_delete=models.CASCADE,
        related_name='cards'
    )

    # Card display info
    card_type = models.CharField(max_length=10, choices=CardType.choices, default=CardType.VIRTUAL)
    card_number = models.CharField(max_length=19, unique=True)
    last_four = models.CharField(max_length=4, default='0000')
    expiry_date = models.CharField(max_length=5, default='01/30')
    cardholder_name = models.CharField(max_length=255, blank=True)

    # Card management
    status = models.CharField(max_length=10, choices=CardStatus.choices, default=CardStatus.ACTIVE)
    color_scheme = models.CharField(max_length=100, default='blue-gradient')
    is_primary = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_primary', '-created_at']

    def __str__(self):
        return f"Card ****{self.last_four}"

    # ?? COMPUTED PROPERTIES
    @property
    def balance(self):
        """Get real balance from Wallet"""
        if hasattr(self.account, 'wallet'):
            return self.account.wallet.balance
        return Decimal('0.00')

    @property
    def account_number(self):
        """Get CLV account number"""
        return self.account.account_number

    @property
    def full_name(self):
        """Get account holder's name from User model"""
        # FIXED: Account IS User in your system (AUTH_USER_MODEL = 'accounts.Account')
        # Direct reference to account which extends AbstractUser
        user = self.account  # This is the Account model instance
        name = f"{user.first_name} {user.last_name}".strip()
        return name if name else user.email

    @property
    def masked_number(self):
        """Format card number for display"""
        if self.last_four and self.last_four != '0000':
            return f"**** **** **** {self.last_four}"
        return "**** **** **** ****"

    @property
    def display_name(self):
        """Get cardholder name (custom or user's name)"""
        return self.cardholder_name or self.full_name


class CardTransaction(models.Model):
    """Track card spending and transactions"""

    # Link to Account and Card
    account = models.ForeignKey(
        'accounts.Account',
        on_delete=models.CASCADE,
        related_name='card_transactions'
    )
    card = models.ForeignKey(
        Card,
        on_delete=models.CASCADE,
        related_name='transactions'
    )

    # Transaction details
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    merchant = models.CharField(max_length=255)
    category = models.CharField(max_length=100, default='other')
    transaction_type = models.CharField(max_length=20, choices=[
        ('credit', 'Credit'),
        ('debit', 'Debit')
    ])
    status = models.CharField(max_length=20, default='completed', choices=[
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('reversed', 'Reversed')
    ])
    description = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_type} ${self.amount} at {self.merchant} ({self.status})"
