"""
cards/models.py - Card models with encryption
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
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cards')
    card_type = models.CharField(max_length=10, choices=CardType.choices, default=CardType.VIRTUAL)
    card_number = models.CharField(max_length=16, unique=True, db_index=True)
    last_four = models.CharField(max_length=4, default='0000')
    cvv = models.CharField(max_length=4, default='000')
    expiry_date = models.CharField(max_length=5, default='01/30')
    cardholder_name = models.CharField(max_length=255, default='Card Holder')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    spending_limit = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('5000.00'), validators=[MinValueValidator(Decimal('0.00'))])
    status = models.CharField(max_length=10, choices=CardStatus.choices, default=CardStatus.ACTIVE)
    color_scheme = models.CharField(max_length=100, default='from-indigo-500 via-purple-500 to-pink-500')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_primary', '-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['card_number']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'is_primary'],
                condition=models.Q(is_primary=True),
                name='unique_primary_card_per_user'
            )
        ]
        verbose_name = "Card"
        verbose_name_plural = "Cards"
    
    def __str__(self):
        return f"{self.card_type.title()} Card - {self.last_four}"
    
    @property
    def masked_number(self):
        """Return masked card number"""
        if self.last_four:
            return f"**** **** **** {self.last_four}"
        return "No card number"
