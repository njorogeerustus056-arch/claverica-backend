"""
cards/models.py - This file is already correct for Django
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal


class CardType(models.TextChoices):
    """Card type choices"""
    VIRTUAL = 'virtual', 'Virtual'
    PHYSICAL = 'physical', 'Physical'


class CardStatus(models.TextChoices):
    """Card status choices"""
    ACTIVE = 'active', 'Active'
    FROZEN = 'frozen', 'Frozen'
    CANCELLED = 'cancelled', 'Cancelled'


class Card(models.Model):
    """Card model for virtual and physical cards"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cards'
    )
    
    # Card details
    card_type = models.CharField(
        max_length=10,
        choices=CardType.choices,
        default=CardType.VIRTUAL
    )
    card_number = models.CharField(max_length=16, unique=True, db_index=True)
    last_four = models.CharField(max_length=4)
    cvv = models.CharField(max_length=3)
    expiry_date = models.CharField(max_length=5)  # Format: MM/YY
    cardholder_name = models.CharField(max_length=255)
    
    # Financial details
    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    spending_limit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('5000.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Card status and appearance
    status = models.CharField(
        max_length=10,
        choices=CardStatus.choices,
        default=CardStatus.ACTIVE
    )
    color_scheme = models.CharField(
        max_length=100,
        default='from-indigo-500 via-purple-500 to-pink-500'
    )
    is_primary = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_primary', '-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['card_number']),
        ]
    
    def __str__(self):
        return f"{self.card_type.title()} Card - {self.last_four}"
    
    @property
    def masked_number(self):
        """Return masked card number"""
        return f"**** **** **** {self.last_four}"


class CardTransaction(models.Model):
    """Transaction model for card and account transactions"""
    
    TRANSACTION_TYPES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    ]
    
    TRANSACTION_STATUS = [
        ('completed', 'Completed'),
        ('pending', 'Pending'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Foreign keys
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='card_transactions'
    )
    card = models.ForeignKey(
        Card,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    
    # Transaction details
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    merchant = models.CharField(max_length=255)
    category = models.CharField(max_length=50, blank=True)
    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPES
    )
    status = models.CharField(
        max_length=20,
        choices=TRANSACTION_STATUS,
        default='completed'
    )
    description = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['card', 'created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.transaction_type.title()} - ${self.amount} - {self.merchant}"