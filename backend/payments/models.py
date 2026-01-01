# payments/models.py - CORRECTED COMPLETE VERSION

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid

User = get_user_model()

# ========== ADD THESE FUNCTIONS ==========
def generate_account_number():
    """Generate unique account number"""
    return str(uuid.uuid4())[:20]

def generate_transaction_id():
    """Generate unique transaction ID"""
    return str(uuid.uuid4())
# =========================================


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
    
    # FIXED: Changed from lambda to function reference
    account_number = models.CharField(max_length=20, unique=True, default=generate_account_number)
    
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='checking')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    available_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, choices=CURRENCIES, default='USD')
    
    # THIS FIELD WAS MISSING - ADDED TO MATCH DATABASE SCHEMA
    is_verified = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.account_type} ({self.account_number})"
    
    def transfer_funds(self, to_account, amount, description=""):
        """Transfer funds between accounts - REQUIRED FOR TESTS"""
        from django.db import transaction as db_transaction
        from decimal import Decimal
        
        if amount <= Decimal('0'):
            raise ValueError("Transfer amount must be positive")
        
        if self.balance < amount:
            raise ValueError("Insufficient funds")
        
        if self.currency != to_account.currency:
            raise ValueError("Currency mismatch")
        
        with db_transaction.atomic():
            # Create transaction records
            debit_tx = Transaction.objects.create(
                account=self,
                amount=amount,
                transaction_type='transfer',
                currency=self.currency,
                description=description,
                status='completed',
                recipient_account=to_account,
                recipient_name=to_account.user.get_full_name() or to_account.user.email
            )
            
            # Update balances
            self.balance -= amount
            self.available_balance -= amount
            self.save()
            
            to_account.balance += amount
            to_account.available_balance += amount
            to_account.save()
            
            return debit_tx


class Transaction(models.Model):
    """Transaction model"""
    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('transfer', 'Transfer'),
        ('payment', 'Payment'),
        ('refund', 'Refund'),
        ('transfer_debit', 'Transfer Debit'),  # Added for transfers
        ('transfer_credit', 'Transfer Credit'),  # Added for transfers
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    
    # FIXED: Changed from lambda to function reference
    transaction_id = models.CharField(max_length=50, unique=True, default=generate_transaction_id)
    
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(max_length=3, default='USD')
    description = models.TextField(blank=True)
    
    # For transfers
    recipient_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_transactions')
    recipient_name = models.CharField(max_length=255, blank=True)
    
    # Add counterparty field for transfers
    counterparty = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='counterparty_transactions')
    
    # Add related transaction field for linking transfers
    related_transaction = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    metadata = models.JSONField(default=dict, blank=True)
    idempotency_key = models.CharField(max_length=100, unique=True, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.transaction_type} - {self.amount} {self.currency} - {self.status}"
    
    class Meta:
        indexes = [
            models.Index(fields=['account', 'created_at']),
            models.Index(fields=['status', 'created_at']),
        ]


class Card(models.Model):
    """Payment card model"""
    CARD_TYPES = [
        ('credit', 'Credit Card'),
        ('debit', 'Debit Card'),
        ('prepaid', 'Prepaid Card'),
    ]
    
    CARD_NETWORKS = [
        ('visa', 'Visa'),
        ('mastercard', 'MasterCard'),
        ('amex', 'American Express'),
        ('discover', 'Discover'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('blocked', 'Blocked'),
        ('expired', 'Expired'),
    ]
    
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='cards')
    card_type = models.CharField(max_length=20, choices=CARD_TYPES)
    card_network = models.CharField(max_length=20, choices=CARD_NETWORKS)
    last_four = models.CharField(max_length=4)
    expiry_month = models.PositiveSmallIntegerField()
    expiry_year = models.PositiveSmallIntegerField()
    card_holder_name = models.CharField(max_length=255)
    token = models.CharField(max_length=100, unique=True)  # Payment gateway token
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_default = models.BooleanField(default=False)
    
    # Security fields (masked in serializers)
    cvv = models.CharField(max_length=4, blank=True)  # Should be encrypted in production
    encrypted_data = models.TextField(blank=True)  # For full encrypted card data
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.card_network} •••• {self.last_four}"
    
    class Meta:
        ordering = ['-is_default', '-created_at']


class PaymentMethod(models.Model):
    """Generic payment method model"""
    PAYMENT_METHOD_TYPES = [
        ('card', 'Card'),
        ('bank_account', 'Bank Account'),
        ('digital_wallet', 'Digital Wallet'),
        ('crypto', 'Cryptocurrency'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    method_type = models.CharField(max_length=20, choices=PAYMENT_METHOD_TYPES)
    display_name = models.CharField(max_length=255)
    is_default = models.BooleanField(default=False)
    
    # References to other models
    card = models.ForeignKey(Card, on_delete=models.CASCADE, null=True, blank=True)
    bank_account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)
    
    # Metadata for different payment methods
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.display_name} ({self.method_type})"


class AuditLog(models.Model):
    """Audit log for tracking important changes"""
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('block', 'Block'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50)
    object_id = models.CharField(max_length=100)
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        user_email = self.user.email if self.user else "System"
        return f"{user_email} - {self.action} - {self.model_name}"
    
    class Meta:
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['user', 'created_at']),
        ]