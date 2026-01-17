# payments/models.py - UPDATED (REMOVED DUPLICATE COMPLIANCE MODELS)
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
from django.utils import timezone

# REMOVED: User = get_user_model() - Use string references instead

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
    
    user = models.ForeignKey('accounts.Account', on_delete=models.CASCADE, related_name='accounts')
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
        ('pending_compliance', 'Pending Compliance'),  # NEW: Waiting for compliance approval
        ('compliance_approved', 'Compliance Approved'),  # NEW: Approved, ready for processing
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
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    metadata = models.JSONField(default=dict, blank=True)
    idempotency_key = models.CharField(max_length=100, unique=True, null=True, blank=True)
    
    # Compliance tracking
    compliance_reference = models.CharField(max_length=100, blank=True)  # Reference to compliance app
    requires_manual_approval = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.transaction_type} - ${self.amount} - {self.status}"
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if self.status == 'completed' and not self.completed_at:
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
    
    user = models.ForeignKey('accounts.Account', on_delete=models.CASCADE, related_name='payment_methods')
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
    user = models.ForeignKey('accounts.Account', on_delete=models.SET_NULL, null=True)
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

# ============================================
# WALLET SYSTEM FOR EMPLOYER-EMPLOYEE PAYMENTS
# ============================================

class MainBusinessWallet(models.Model):
    """Main business wallet for employers/companies"""
    WALLET_TYPES = [
        ('employer', 'Employer/Company'),
        ('business', 'Business Account'),
        ('corporate', 'Corporate Account'),
    ]
    
    # Link to user (employer/company owner)
    user = models.OneToOneField(
        'accounts.Account',
        on_delete=models.CASCADE,
        related_name='main_business_wallet'
    )
    
    # Wallet identification
    wallet_type = models.CharField(max_length=20, choices=WALLET_TYPES, default='employer')
    wallet_number = models.CharField(max_length=20, unique=True, default=generate_account_number)
    display_name = models.CharField(max_length=100, default="Main Business Wallet")
    
    # Balance tracking
    total_balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    available_balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=3, choices=Account.CURRENCIES, default='USD')
    
    # Bank connection (Goldman Sachs)
    connected_bank_name = models.CharField(max_length=100, default="The Goldman Sachs Group")
    connected_bank_account = models.CharField(max_length=50, blank=True)
    connected_bank_routing = models.CharField(max_length=20, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    auto_replenish = models.BooleanField(default=False)
    min_balance_threshold = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('1000.00'))
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.wallet_number} - {self.display_name} - ${self.total_balance}"
    
    def save(self, *args, **kwargs):
        if not self.wallet_number:
            self.wallet_number = f"MBW{self.user.id:08d}{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    def has_sufficient_funds(self, amount):
        """Check if wallet has sufficient funds"""
        return self.available_balance >= Decimal(str(amount))
    
    def deduct_funds(self, amount, description="Payment to employee"):
        """Deduct funds from main wallet"""
        amount_decimal = Decimal(str(amount))
        
        if not self.has_sufficient_funds(amount_decimal):
            raise ValueError(f"Insufficient funds. Available: ${self.available_balance}, Required: ${amount}")
        
        self.total_balance -= amount_decimal
        self.available_balance -= amount_decimal
        self.save()
        
        return amount_decimal


class EmployeePlatformWallet(models.Model):
    """Platform wallet for employees to receive payments"""
    WALLET_STATUS = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('closed', 'Closed'),
    ]
    
    # Link to user (employee)
    user = models.OneToOneField(
        'accounts.Account',
        on_delete=models.CASCADE,
        related_name='employee_platform_wallet'
    )
    
    # Wallet identification
    wallet_number = models.CharField(max_length=20, unique=True, default=generate_account_number)
    display_name = models.CharField(max_length=100, default="ClaveRica Wallet")
    
    # Balance tracking
    platform_balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    available_for_withdrawal = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    pending_withdrawal = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=3, choices=Account.CURRENCIES, default='USD')
    
    # Withdrawal settings
    preferred_bank = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='preferred_withdrawal_accounts'
    )
    auto_withdraw_enabled = models.BooleanField(default=False)
    withdraw_threshold = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('100.00'))
    
    # Status
    status = models.CharField(max_length=20, choices=WALLET_STATUS, default='active')
    last_withdrawal_date = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.wallet_number} - {self.user.email} - ${self.platform_balance}"
    
    def save(self, *args, **kwargs):
        if not self.wallet_number:
            self.wallet_number = f"EPW{self.user.id:08d}{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    def add_funds(self, amount, source="employer_payment"):
        """Add funds to employee wallet"""
        amount_decimal = Decimal(str(amount))
        
        self.platform_balance += amount_decimal
        self.available_for_withdrawal += amount_decimal
        self.save()
        
        return amount_decimal
    
    def request_withdrawal(self, amount, bank_account=None):
        """Request withdrawal from platform wallet to bank"""
        amount_decimal = Decimal(str(amount))
        
        if amount_decimal > self.available_for_withdrawal:
            raise ValueError(f"Insufficient withdrawal balance. Available: ${self.available_for_withdrawal}")
        
        # Create withdrawal request
        withdrawal = WithdrawalRequest.objects.create(
            employee_wallet=self,
            amount=amount_decimal,
            bank_account=bank_account or self.preferred_bank,
            status='pending'
        )
        
        # Lock funds
        self.available_for_withdrawal -= amount_decimal
        self.pending_withdrawal += amount_decimal
        self.save()
        
        return withdrawal


class PaymentTransactionNotification(models.Model):
    """Store formatted payment notifications for employees"""
    NOTIFICATION_TYPES = [
        ('payment_received', 'Payment Received'),
        ('withdrawal_requested', 'Withdrawal Requested'),
        ('withdrawal_completed', 'Withdrawal Completed'),
        ('compliance_required', 'Compliance Required'),
    ]
    
    # Reference tracking
    reference_code = models.CharField(max_length=20, unique=True)  # MBNHLF9RR42TSAO3
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True
    )
    
    # User information
    sender = models.ForeignKey(
        'accounts.Account',
        on_delete=models.CASCADE,
        related_name='sent_notifications'
    )
    receiver = models.ForeignKey(
        'accounts.Account',
        on_delete=models.CASCADE,
        related_name='received_notifications'
    )
    
    # Notification content
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Formatted messages
    full_message = models.TextField()  # Complete notification text
    short_message = models.CharField(max_length=200)  # For dashboard
    emoji = models.CharField(max_length=10, default='😊')
    
    # Account details
    sender_account = models.CharField(max_length=50, blank=True)  # ecoveraLTD
    receiver_account = models.CharField(max_length=50, blank=True)
    bank_routing = models.CharField(max_length=100, default="via ClaveRica branch - The Goldman Sachs Group")
    
    # Delivery status
    email_sent = models.BooleanField(default=False)
    push_sent = models.BooleanField(default=False)
    website_delivered = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reference_code']),
            models.Index(fields=['receiver', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.reference_code} - {self.notification_type} - ${self.amount}"
    
    def generate_reference_code(self):
        """Generate unique reference code like MBNHLF9RR42TSAO3"""
        import random
        import string
        
        # Format: 16 chars, mixed case
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(16))
    
    def save(self, *args, **kwargs):
        if not self.reference_code:
            self.reference_code = self.generate_reference_code()
        super().save(*args, **kwargs)


class WithdrawalRequest(models.Model):
    """Employee withdrawal requests with compliance tracking"""
    WITHDRAWAL_STATUS = [
        ('pending', 'Pending'),
        ('compliance_check', 'Compliance Check'),
        ('agent_call', 'Agent Video Call'),
        ('tac_verification', 'TAC Verification'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Wallet link
    employee_wallet = models.ForeignKey(
        EmployeePlatformWallet,
        on_delete=models.CASCADE,
        related_name='withdrawal_requests'
    )
    
    # Withdrawal details
    withdrawal_reference = models.CharField(max_length=20, unique=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Bank destination
    bank_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='withdrawal_requests'
    )
    
    # Compliance tracking
    status = models.CharField(max_length=30, choices=WITHDRAWAL_STATUS, default='pending')
    compliance_form_filled = models.BooleanField(default=False)
    agent_call_scheduled = models.BooleanField(default=False)
    agent_call_completed = models.BooleanField(default=False)
    
    # TAC verification
    tac_code = models.CharField(max_length=10, null=True, blank=True)
    tac_generated_at = models.DateTimeField(null=True, blank=True)
    tac_verified_at = models.DateTimeField(null=True, blank=True)
    
    # Agent information
    assigned_agent = models.ForeignKey(
        'accounts.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_withdrawals'
    )
    agent_call_date = models.DateTimeField(null=True, blank=True)
    agent_call_duration = models.IntegerField(null=True, blank=True)  # in seconds
    agent_notes = models.TextField(blank=True)
    
    # Processing
    processed_at = models.DateTimeField(null=True, blank=True)
    transaction_reference = models.CharField(max_length=50, blank=True)
    
    # Compliance reference (NEW: Links to central compliance app)
    compliance_request_id = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.withdrawal_reference} - ${self.amount} - {self.status}"
    
    def save(self, *args, **kwargs):
        if not self.withdrawal_reference:
            self.withdrawal_reference = f"WDR{self.employee_wallet.user.id:08d}{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    def generate_tac_code(self):
        """Generate TAC code for withdrawal authorization"""
        import random
        
        # Generate 6-digit TAC
        tac = ''.join(str(random.randint(0, 9)) for _ in range(6))
        self.tac_code = tac
        self.tac_generated_at = timezone.now()
        self.save()
        
        return tac


class ActivityFeed(models.Model):
    """Dashboard activity feed with emoji indicators"""
    ACTIVITY_TYPES = [
        ('payment_received', '↑ Payment Received'),
        ('payment_sent', '↓ Payment Sent'),
        ('withdrawal_request', '🏦 Withdrawal Request'),
        ('withdrawal_completed', '✅ Withdrawal Completed'),
        ('compliance_started', '⏳ Compliance Started'),
        ('agent_call', '📞 Agent Call'),
    ]
    
    user = models.ForeignKey(
        'accounts.Account',
        on_delete=models.CASCADE,
        related_name='activity_feed'
    )
    
    # Activity details
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES)
    reference = models.CharField(max_length=20, blank=True)  # Link to transaction/withdrawal
    amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    
    # Display properties
    display_text = models.CharField(max_length=200)  # "↑ +$10,000 (ClaveRica LTD)"
    emoji = models.CharField(max_length=10, default='😊')
    color_class = models.CharField(max_length=50, default='text-green-600')  # For frontend styling
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)  # Auto-remove after X days
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.activity_type} - {self.display_text}"