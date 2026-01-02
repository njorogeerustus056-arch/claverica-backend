# payments/models.py - UPDATED TO MATCH DATABASE SCHEMA
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid

User = get_user_model()

def generate_account_number():
    """Generate unique account number"""
    return str(uuid.uuid4()).replace('-', '')[:20].upper()

def generate_transaction_id():
    """Generate unique transaction ID"""
    return str(uuid.uuid4())


class Account(models.Model):
    """Bank account model"""
    ACCOUNT_TYPES = [
        ('checking', 'Checking'),
        ('savings', 'Savings'),
        ('business', 'Business'),
    ]
    
    CURRENCIES = [
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accounts')
    account_number = models.CharField(max_length=20, unique=True, default=generate_account_number)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='checking')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    available_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=3, choices=CURRENCIES, default='USD')
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.account_number} - {self.account_type} - ${self.balance}"
    
    def transfer_funds(self, to_account, amount, description=""):
        """Transfer funds between accounts"""
        from django.db import transaction as db_transaction
        
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        
        if amount <= Decimal('0'):
            raise ValueError("Transfer amount must be positive")
        
        if self.available_balance < amount:
            raise ValueError(f"Insufficient funds. Available: ${self.available_balance}, Required: ${amount}")
        
        if self.currency != to_account.currency:
            raise ValueError(f"Currency mismatch. Source: {self.currency}, Target: {to_account.currency}")
        
        if not self.is_active:
            raise ValueError("Source account is not active")
        
        if not to_account.is_active:
            raise ValueError("Target account is not active")
        
        # Use database transaction for atomicity
        with db_transaction.atomic():
            # Lock accounts for update
            source_account = Account.objects.select_for_update().get(pk=self.pk)
            target_account = Account.objects.select_for_update().get(pk=to_account.pk)
            
            # Double-check balance after locking
            if source_account.available_balance < amount:
                raise ValueError(f"Insufficient funds after lock")
            
            # Create transaction record
            transaction = Transaction.objects.create(
                account=source_account,
                recipient_account=target_account,
                amount=amount,
                currency=source_account.currency,
                transaction_type='transfer',
                description=description,
                status='completed'
            )
            
            # Update balances
            source_account.balance -= amount
            source_account.available_balance -= amount
            source_account.save()
            
            target_account.balance += amount
            target_account.available_balance += amount
            target_account.save()
            
            return transaction


class Transaction(models.Model):
    """Transaction model"""
    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('transfer', 'Transfer'),
        ('payment', 'Payment'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    account = models.ForeignKey(
        Account, 
        on_delete=models.CASCADE, 
        related_name='transactions'
    )
    
    recipient_account = models.ForeignKey(
        Account, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='received_transactions'
    )
    
    transaction_id = models.CharField(max_length=50, unique=True, default=generate_transaction_id)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(max_length=3, default='USD')
    description = models.TextField(blank=True)
    recipient_name = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    metadata = models.JSONField(default=dict, blank=True)
    idempotency_key = models.CharField(max_length=100, unique=True, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.transaction_type} - ${self.amount} - {self.status}"
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if self.status == 'completed' and not self.completed_at:
            from django.utils import timezone
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)


class Card(models.Model):
    """Payment card model"""
    CARD_TYPES = [
        ('credit', 'Credit Card'),
        ('debit', 'Debit Card'),
    ]
    
    CARD_NETWORKS = [
        ('visa', 'Visa'),
        ('mastercard', 'MasterCard'),
        ('amex', 'American Express'),
        ('discover', 'Discover'),
    ]
    
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='cards')
    card_type = models.CharField(max_length=20, choices=CARD_TYPES)
    card_network = models.CharField(max_length=20, choices=CARD_NETWORKS, default='visa')
    last_four = models.CharField(max_length=4)
    expiry_month = models.PositiveSmallIntegerField()
    expiry_year = models.PositiveSmallIntegerField()
    card_holder_name = models.CharField(max_length=255)
    token = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, default='active')
    is_default = models.BooleanField(default=False)
    cvv = models.CharField(max_length=4, blank=True, default="")
    encrypted_data = models.TextField(blank=True, default="")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.card_network} •••• {self.last_four}"
    
    def is_expired(self):
        import datetime
        current_year = datetime.datetime.now().year
        current_month = datetime.datetime.now().month
        return (self.expiry_year < current_year) or (self.expiry_year == current_year and self.expiry_month < current_month)


class PaymentMethod(models.Model):
    """Payment method model"""
    METHOD_TYPES = [
        ('card', 'Card'),
        ('bank', 'Bank Account'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    method_type = models.CharField(max_length=20, choices=METHOD_TYPES)
    display_name = models.CharField(max_length=255)
    is_default = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    
    # References to actual payment methods
    bank_account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)
    card = models.ForeignKey(Card, on_delete=models.CASCADE, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.display_name} ({self.method_type})"


class AuditLog(models.Model):
    """Audit log model"""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50)
    model_name = models.CharField(max_length=50, blank=True, default="")
    object_id = models.CharField(max_length=100, blank=True, default="")
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.email if self.user else 'System'} - {self.action}"
    
    class Meta:
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['user', 'created_at']),
        ]