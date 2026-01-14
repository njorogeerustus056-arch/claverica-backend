# crypto/models.py - UPDATED FOR CENTRALIZED COMPLIANCE

from django.db import models
from django.conf import settings
import uuid
from decimal import Decimal


class TransactionType(models.TextChoices):
    BUY = "buy", "Buy"
    SELL = "sell", "Sell"
    SEND = "send", "Send"
    RECEIVE = "receive", "Receive"
    SWAP = "swap", "Swap"
    DEPOSIT = "deposit", "Deposit"
    WITHDRAWAL = "withdrawal", "Withdrawal"


class TransactionStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"
    PENDING_COMPLIANCE = "pending_compliance", "Pending Compliance"
    COMPLIANCE_APPROVED = "compliance_approved", "Compliance Approved"
    COMPLIANCE_REJECTED = "compliance_rejected", "Compliance Rejected"


class WalletType(models.TextChoices):
    HOT = "hot", "Hot Wallet"
    COLD = "cold", "Cold Wallet"
    CUSTODIAL = "custodial", "Custodial"
    NON_CUSTODIAL = "non_custodial", "Non-Custodial"


class ComplianceStatus(models.TextChoices):
    NOT_REQUIRED = "not_required", "Not Required"
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    FLAGGED = "flagged", "Flagged for Review"
    UNDER_REVIEW = "under_review", "Under Review"


class CryptoAsset(models.Model):
    """Model for supported cryptocurrencies"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Asset Details
    symbol = models.CharField(max_length=10, unique=True, db_index=True)
    name = models.CharField(max_length=100)
    logo = models.CharField(max_length=255, blank=True, null=True)
    
    # Blockchain Details
    blockchain = models.CharField(max_length=50, default="ethereum")
    contract_address = models.CharField(max_length=255, blank=True, null=True)
    decimals = models.IntegerField(default=18)
    
    # Market Data
    current_price_usd = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    market_cap = models.DecimalField(max_digits=30, decimal_places=2, blank=True, null=True)
    volume_24h = models.DecimalField(max_digits=30, decimal_places=2, blank=True, null=True)
    change_24h = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    change_7d = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    change_30d = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    
    # Trading Info
    is_tradable = models.BooleanField(default=True)
    is_depositable = models.BooleanField(default=True)
    is_withdrawable = models.BooleanField(default=True)
    min_deposit = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    min_withdrawal = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    withdrawal_fee = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Metadata
    description = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    explorer_url = models.URLField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_price_update = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ["-market_cap"]
        indexes = [
            models.Index(fields=["symbol"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["blockchain"]),
        ]
    
    def __str__(self):
        return f"{self.symbol} - {self.name}"


class CryptoWallet(models.Model):
    """Model for user crypto wallets"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="crypto_wallets")
    asset = models.ForeignKey(CryptoAsset, on_delete=models.CASCADE, related_name="wallets")
    
    # Wallet Details
    wallet_address = models.CharField(max_length=255)
    wallet_type = models.CharField(max_length=20, choices=WalletType.choices, default=WalletType.HOT)
    label = models.CharField(max_length=100, blank=True, null=True)
    
    # Balance
    balance = models.DecimalField(max_digits=30, decimal_places=8, default=0)
    available_balance = models.DecimalField(max_digits=30, decimal_places=8, default=0)
    locked_balance = models.DecimalField(max_digits=30, decimal_places=8, default=0)
    
    # Balance in USD
    balance_usd = models.DecimalField(max_digits=30, decimal_places=2, default=0)
    
    # COMPLIANCE INTEGRATION FIELDS
    compliance_reference = models.CharField(max_length=100, blank=True, null=True)
    requires_compliance_approval = models.BooleanField(default=False)
    compliance_status = models.CharField(
        max_length=20, 
        choices=ComplianceStatus.choices, 
        default=ComplianceStatus.NOT_REQUIRED
    )
    is_suspicious = models.BooleanField(default=False)
    
    # Security (encrypted fields)
    encrypted_private_key = models.TextField(blank=True, null=True)
    public_key = models.TextField(blank=True, null=True)
    mnemonic_encrypted = models.TextField(blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    
    # Metadata
    metadata = models.JSONField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_transaction_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        unique_together = ["user", "asset"]
        indexes = [
            models.Index(fields=["user", "asset"]),
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["wallet_address"]),
            models.Index(fields=["compliance_reference"]),  # NEW
            models.Index(fields=["compliance_status"]),  # NEW
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.asset.symbol} Wallet"
    
    def calculate_balance_usd(self):
        """Calculate USD value of wallet balance"""
        if self.asset.current_price_usd:
            self.balance_usd = self.balance * self.asset.current_price_usd
        return self.balance_usd
    
    def save(self, *args, **kwargs):
        self.calculate_balance_usd()
        
        # Auto-flag suspicious wallet activities
        if self.balance_usd > Decimal('100000'):  # $100K in crypto
            self.requires_compliance_approval = True
            self.compliance_status = ComplianceStatus.PENDING
        
        super().save(*args, **kwargs)


class CryptoTransaction(models.Model):
    """Model for crypto transactions"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="crypto_transactions")
    asset = models.ForeignKey(CryptoAsset, on_delete=models.CASCADE, related_name="transactions")
    
    # Transaction Type
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    status = models.CharField(max_length=30, choices=TransactionStatus.choices, default=TransactionStatus.PENDING)
    
    # Wallet Information
    from_wallet = models.ForeignKey(
        CryptoWallet, 
        on_delete=models.CASCADE, 
        related_name="sent_transactions",
        blank=True, 
        null=True
    )
    to_wallet = models.ForeignKey(
        CryptoWallet, 
        on_delete=models.CASCADE, 
        related_name="received_transactions",
        blank=True, 
        null=True
    )
    from_address = models.CharField(max_length=255, blank=True, null=True)
    to_address = models.CharField(max_length=255, blank=True, null=True)
    
    # Amount Details
    amount = models.DecimalField(max_digits=30, decimal_places=8)
    amount_usd = models.DecimalField(max_digits=30, decimal_places=2, blank=True, null=True)
    fee = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    fee_usd = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    network_fee = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    
    # Price at transaction time
    price_at_transaction = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    
    # COMPLIANCE INTEGRATION FIELDS
    compliance_reference = models.CharField(max_length=100, blank=True, null=True)
    requires_compliance_approval = models.BooleanField(default=False)
    compliance_status = models.CharField(
        max_length=20, 
        choices=ComplianceStatus.choices, 
        default=ComplianceStatus.NOT_REQUIRED
    )
    is_high_value = models.BooleanField(default=False)
    is_suspicious = models.BooleanField(default=False)
    compliance_notes = models.TextField(blank=True, null=True)
    
    # Blockchain Details
    transaction_hash = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    block_number = models.BigIntegerField(blank=True, null=True)
    confirmations = models.IntegerField(default=0)
    required_confirmations = models.IntegerField(default=6)
    
    # Gas Details (for EVM chains)
    gas_price = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    gas_used = models.BigIntegerField(blank=True, null=True)
    gas_limit = models.BigIntegerField(blank=True, null=True)
    
    # Swap Details
    swap_from_asset = models.ForeignKey(
        CryptoAsset, 
        on_delete=models.SET_NULL, 
        related_name="swap_from_transactions",
        blank=True, 
        null=True
    )
    swap_to_asset = models.ForeignKey(
        CryptoAsset, 
        on_delete=models.SET_NULL, 
        related_name="swap_to_transactions",
        blank=True, 
        null=True
    )
    swap_rate = models.DecimalField(max_digits=30, decimal_places=8, blank=True, null=True)
    
    # Status Details
    error_message = models.TextField(blank=True, null=True)
    retry_count = models.IntegerField(default=0)
    
    # Metadata
    description = models.TextField(blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True)
    
    # Security
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["transaction_hash"]),
            models.Index(fields=["compliance_reference"]),  # NEW
            models.Index(fields=["compliance_status"]),  # NEW
            models.Index(fields=["is_high_value"]),  # NEW
            models.Index(fields=["is_suspicious"]),  # NEW
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.transaction_type} - {self.amount} {self.asset.symbol}"
    
    def calculate_amount_usd(self):
        """Calculate USD value of transaction amount"""
        if self.price_at_transaction:
            self.amount_usd = self.amount * self.price_at_transaction
        elif self.asset.current_price_usd:
            self.amount_usd = self.amount * self.asset.current_price_usd
        return self.amount_usd
    
    def save(self, *args, **kwargs):
        if not self.price_at_transaction and self.asset.current_price_usd:
            self.price_at_transaction = self.asset.current_price_usd
        self.calculate_amount_usd()
        
        # Auto-flag high-value transactions (> $10,000 USD equivalent)
        if self.amount_usd and self.amount_usd > Decimal('10000'):
            self.is_high_value = True
            self.requires_compliance_approval = True
            if self.status == TransactionStatus.PENDING:
                self.status = TransactionStatus.PENDING_COMPLIANCE
                self.compliance_status = ComplianceStatus.PENDING
        
        # Auto-flag suspicious withdrawals to new addresses
        if (self.transaction_type in [TransactionType.WITHDRAWAL, TransactionType.SEND] and 
            self.to_address and 
            not self.to_wallet and 
            self.amount_usd and 
            self.amount_usd > Decimal('1000')):  # > $1K to new address
            self.is_suspicious = True
            self.requires_compliance_approval = True
            if self.status == TransactionStatus.PENDING:
                self.status = TransactionStatus.PENDING_COMPLIANCE
        
        super().save(*args, **kwargs)
    
    def mark_as_compliance_approved(self):
        """Mark transaction as approved by compliance"""
        self.compliance_status = ComplianceStatus.APPROVED
        self.requires_compliance_approval = False
        if self.status == TransactionStatus.PENDING_COMPLIANCE:
            self.status = TransactionStatus.COMPLIANCE_APPROVED
        self.save()
    
    def mark_as_compliance_rejected(self, notes=""):
        """Mark transaction as rejected by compliance"""
        self.compliance_status = ComplianceStatus.REJECTED
        self.compliance_notes = notes
        if self.status == TransactionStatus.PENDING_COMPLIANCE:
            self.status = TransactionStatus.COMPLIANCE_REJECTED
        self.save()


class CryptoComplianceFlag(models.Model):
    """Track crypto compliance flags and AML alerts"""
    FLAG_TYPES = [
        ('high_value', 'High Value Transaction'),
        ('new_address', 'Withdrawal to New Address'),
        ('suspicious_pattern', 'Suspicious Pattern'),
        ('aml_alert', 'AML Alert'),
        ('sanctions_match', 'Sanctions List Match'),
        ('pep_match', 'PEP (Politically Exposed Person)'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    transaction = models.ForeignKey(CryptoTransaction, on_delete=models.CASCADE, 
                                   related_name="compliance_flags")
    flag_type = models.CharField(max_length=50, choices=FLAG_TYPES)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    description = models.TextField()
    indicators = models.JSONField(blank=True, null=True)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(blank=True, null=True)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    resolution_notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.flag_type} - {self.transaction.id}"


class CryptoAuditLog(models.Model):
    """Audit log for crypto operations with compliance tracking"""
    ACTION_CHOICES = [
        ('wallet_created', 'Wallet Created'),
        ('transaction_created', 'Transaction Created'),
        ('transaction_updated', 'Transaction Updated'),
        ('compliance_requested', 'Compliance Requested'),
        ('compliance_approved', 'Compliance Approved'),
        ('compliance_rejected', 'Compliance Rejected'),
        ('flag_created', 'Compliance Flag Created'),
        ('flag_resolved', 'Compliance Flag Resolved'),
        ('kyc_requested', 'KYC Requested'),
        ('tac_generated', 'TAC Generated'),
        ('tac_verified', 'TAC Verified'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    transaction = models.ForeignKey(CryptoTransaction, on_delete=models.SET_NULL, 
                                   null=True, blank=True)
    wallet = models.ForeignKey(CryptoWallet, on_delete=models.SET_NULL, 
                              null=True, blank=True)
    details = models.JSONField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email if self.user else 'System'} - {self.action}"