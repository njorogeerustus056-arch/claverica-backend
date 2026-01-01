from django.db import models
from django.conf import settings
import uuid


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


class WalletType(models.TextChoices):
    HOT = "hot", "Hot Wallet"
    COLD = "cold", "Cold Wallet"
    CUSTODIAL = "custodial", "Custodial"
    NON_CUSTODIAL = "non_custodial", "Non-Custodial"


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
        super().save(*args, **kwargs)


class CryptoTransaction(models.Model):
    """Model for crypto transactions"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="crypto_transactions")
    asset = models.ForeignKey(CryptoAsset, on_delete=models.CASCADE, related_name="transactions")
    
    # Transaction Type
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    status = models.CharField(max_length=20, choices=TransactionStatus.choices, default=TransactionStatus.PENDING)
    
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
        super().save(*args, **kwargs)


class PriceHistory(models.Model):
    """Model for cryptocurrency price history"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey(CryptoAsset, on_delete=models.CASCADE, related_name="price_history")
    
    # Price Data
    price_usd = models.DecimalField(max_digits=20, decimal_places=8)
    volume_24h = models.DecimalField(max_digits=30, decimal_places=2, blank=True, null=True)
    market_cap = models.DecimalField(max_digits=30, decimal_places=2, blank=True, null=True)
    
    # OHLC Data
    open_price = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    high_price = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    low_price = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    close_price = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    
    # Timestamp
    timestamp = models.DateTimeField(db_index=True)
    interval = models.CharField(max_length=10, default="1h")  # 1m, 5m, 15m, 1h, 4h, 1d
    
    class Meta:
        ordering = ["-timestamp"]
        unique_together = ["asset", "timestamp", "interval"]
        indexes = [
            models.Index(fields=["asset", "timestamp"]),
        ]
    
    def __str__(self):
        return f"{self.asset.symbol} - {self.price_usd} USD - {self.timestamp}"


class CryptoAddress(models.Model):
    """Model for storing crypto addresses"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="crypto_addresses")
    asset = models.ForeignKey(CryptoAsset, on_delete=models.CASCADE, related_name="addresses")
    
    # Address Details
    address = models.CharField(max_length=255, unique=True, db_index=True)
    label = models.CharField(max_length=100, blank=True, null=True)
    address_type = models.CharField(max_length=50, blank=True, null=True)  # deposit, withdrawal, personal
    
    # Verification
    is_verified = models.BooleanField(default=False)
    is_whitelisted = models.BooleanField(default=False)
    
    # Security
    verification_code = models.CharField(max_length=10, blank=True, null=True)
    verified_at = models.DateTimeField(blank=True, null=True)
    
    # Metadata
    metadata = models.JSONField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "asset"]),
            models.Index(fields=["address"]),
            models.Index(fields=["is_verified"]),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.asset.symbol} - {self.address[:10]}..."


class FiatPlatform(models.Model):
    """Model for fiat platforms (banks, payment processors)"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Platform Details
    name = models.CharField(max_length=100, unique=True)
    logo = models.CharField(max_length=255, blank=True, null=True)
    platform_type = models.CharField(max_length=50)  # bank, payment
    
    # Support
    supported_currencies = models.JSONField(default=list)  # ["USD", "EUR", "GBP"]
    supported_countries = models.JSONField(default=list)
    
    # Features
    supports_deposits = models.BooleanField(default=True)
    supports_withdrawals = models.BooleanField(default=True)
    
    # Fees
    deposit_fee = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    withdrawal_fee = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    
    # Limits
    min_deposit = models.DecimalField(max_digits=20, decimal_places=4, blank=True, null=True)
    max_deposit = models.DecimalField(max_digits=20, decimal_places=4, blank=True, null=True)
    min_withdrawal = models.DecimalField(max_digits=20, decimal_places=4, blank=True, null=True)
    max_withdrawal = models.DecimalField(max_digits=20, decimal_places=4, blank=True, null=True)
    
    # Processing Time
    deposit_processing_time = models.CharField(max_length=50, blank=True, null=True)  # "instant", "1-3 days"
    withdrawal_processing_time = models.CharField(max_length=50, blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["name"]
    
    def __str__(self):
        return self.name


class UserFiatAccount(models.Model):
    """Model for user fiat accounts linked to platforms"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="fiat_accounts")
    platform = models.ForeignKey(FiatPlatform, on_delete=models.CASCADE, related_name="user_accounts")
    
    # Account Details
    account_number = models.CharField(max_length=255, blank=True, null=True)
    account_holder = models.CharField(max_length=255)
    
    # Balance
    balance = models.DecimalField(max_digits=30, decimal_places=4, default=0)
    currency = models.CharField(max_length=3)  # USD, EUR, GBP
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(blank=True, null=True)
    
    # Metadata
    metadata = models.JSONField(blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ["user", "platform", "account_number"]
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["platform", "currency"]),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.platform.name} - {self.currency}"