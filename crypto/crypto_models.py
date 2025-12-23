from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Float, JSON, Enum as SQLEnum, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from database import Base
import enum
import uuid

class TransactionType(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"
    SEND = "send"
    RECEIVE = "receive"
    SWAP = "swap"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"

class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class WalletType(str, enum.Enum):
    HOT = "hot"
    COLD = "cold"
    CUSTODIAL = "custodial"
    NON_CUSTODIAL = "non_custodial"

class CryptoAsset(Base):
    __tablename__ = "crypto_assets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Asset Details
    symbol = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    logo = Column(String(255), nullable=True)
    
    # Blockchain Details
    blockchain = Column(String(50), nullable=False)  # ethereum, bitcoin, binance_smart_chain
    contract_address = Column(String(255), nullable=True)  # For tokens
    decimals = Column(Integer, default=18)
    
    # Market Data
    current_price_usd = Column(Float, default=0.0)
    market_cap = Column(Float, nullable=True)
    volume_24h = Column(Float, nullable=True)
    change_24h = Column(Float, default=0.0)
    change_7d = Column(Float, default=0.0)
    change_30d = Column(Float, default=0.0)
    
    # Trading Info
    is_tradable = Column(Boolean, default=True)
    is_depositable = Column(Boolean, default=True)
    is_withdrawable = Column(Boolean, default=True)
    min_deposit = Column(Float, nullable=True)
    min_withdrawal = Column(Float, nullable=True)
    withdrawal_fee = Column(Float, default=0.0)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Metadata
    description = Column(Text, nullable=True)
    website = Column(String(255), nullable=True)
    explorer_url = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_price_update = Column(DateTime, nullable=True)
    
    # Relationships
    wallets = relationship("CryptoWallet", back_populates="asset")
    transactions = relationship("CryptoTransaction", back_populates="asset")


class CryptoWallet(Base):
    __tablename__ = "crypto_wallets"
    
    __table_args__ = (
        Index('idx_user_asset', 'user_id', 'asset_id'),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    asset_id = Column(String, ForeignKey("crypto_assets.id"), nullable=False)
    
    # Wallet Details
    wallet_address = Column(String(255), nullable=False)
    wallet_type = Column(SQLEnum(WalletType), default=WalletType.HOT)
    label = Column(String(100), nullable=True)
    
    # Balance
    balance = Column(Float, default=0.0)
    available_balance = Column(Float, default=0.0)
    locked_balance = Column(Float, default=0.0)
    
    # Balance in USD
    balance_usd = Column(Float, default=0.0)
    
    # Security
    encrypted_private_key = Column(Text, nullable=True)  # Encrypted
    public_key = Column(Text, nullable=True)
    mnemonic_encrypted = Column(Text, nullable=True)  # Encrypted seed phrase
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_transaction_at = Column(DateTime, nullable=True)
    
    # Relationships
    asset = relationship("CryptoAsset", back_populates="wallets")
    transactions_sent = relationship(
        "CryptoTransaction",
        foreign_keys="CryptoTransaction.from_wallet_id",
        back_populates="from_wallet"
    )
    transactions_received = relationship(
        "CryptoTransaction",
        foreign_keys="CryptoTransaction.to_wallet_id",
        back_populates="to_wallet"
    )


class CryptoTransaction(Base):
    __tablename__ = "crypto_transactions"
    
    __table_args__ = (
        Index('idx_user_status', 'user_id', 'status'),
        Index('idx_user_created', 'user_id', 'created_at'),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    asset_id = Column(String, ForeignKey("crypto_assets.id"), nullable=False)
    
    # Transaction Type
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.PENDING)
    
    # Wallet Information
    from_wallet_id = Column(String, ForeignKey("crypto_wallets.id"), nullable=True)
    to_wallet_id = Column(String, ForeignKey("crypto_wallets.id"), nullable=True)
    from_address = Column(String(255), nullable=True)
    to_address = Column(String(255), nullable=True)
    
    # Amount Details
    amount = Column(Float, nullable=False)
    amount_usd = Column(Float, nullable=True)
    fee = Column(Float, default=0.0)
    fee_usd = Column(Float, default=0.0)
    network_fee = Column(Float, default=0.0)
    
    # Price at transaction time
    price_at_transaction = Column(Float, nullable=True)
    
    # Blockchain Details
    transaction_hash = Column(String(255), nullable=True, index=True)
    block_number = Column(Integer, nullable=True)
    confirmations = Column(Integer, default=0)
    required_confirmations = Column(Integer, default=6)
    
    # Gas Details (for EVM chains)
    gas_price = Column(Float, nullable=True)
    gas_used = Column(Integer, nullable=True)
    gas_limit = Column(Integer, nullable=True)
    
    # Swap Details (if transaction_type is SWAP)
    swap_from_asset_id = Column(String, ForeignKey("crypto_assets.id"), nullable=True)
    swap_to_asset_id = Column(String, ForeignKey("crypto_assets.id"), nullable=True)
    swap_rate = Column(Float, nullable=True)
    
    # Status Details
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Metadata
    description = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # Security
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    
    # Relationships
    asset = relationship("CryptoAsset", foreign_keys=[asset_id], back_populates="transactions")
    from_wallet = relationship("CryptoWallet", foreign_keys=[from_wallet_id], back_populates="transactions_sent")
    to_wallet = relationship("CryptoWallet", foreign_keys=[to_wallet_id], back_populates="transactions_received")


class PriceHistory(Base):
    __tablename__ = "price_history"
    
    __table_args__ = (
        Index('idx_asset_timestamp', 'asset_id', 'timestamp'),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_id = Column(String, ForeignKey("crypto_assets.id"), nullable=False)
    
    # Price Data
    price_usd = Column(Float, nullable=False)
    volume_24h = Column(Float, nullable=True)
    market_cap = Column(Float, nullable=True)
    
    # OHLC Data
    open_price = Column(Float, nullable=True)
    high_price = Column(Float, nullable=True)
    low_price = Column(Float, nullable=True)
    close_price = Column(Float, nullable=True)
    
    # Timestamp
    timestamp = Column(DateTime, nullable=False, index=True)
    interval = Column(String(10), default="1h")  # 1m, 5m, 15m, 1h, 4h, 1d


class CryptoAddress(Base):
    __tablename__ = "crypto_addresses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    asset_id = Column(String, ForeignKey("crypto_assets.id"), nullable=False)
    
    # Address Details
    address = Column(String(255), nullable=False, unique=True, index=True)
    label = Column(String(100), nullable=True)
    address_type = Column(String(50), nullable=True)  # deposit, withdrawal, personal
    
    # Verification
    is_verified = Column(Boolean, default=False)
    is_whitelisted = Column(Boolean, default=False)
    
    # Security
    verification_code = Column(String(10), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)


class FiatPlatform(Base):
    __tablename__ = "fiat_platforms"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Platform Details
    name = Column(String(100), nullable=False, unique=True)
    logo = Column(String(255), nullable=True)
    platform_type = Column(String(50), nullable=False)  # bank, payment
    
    # Support
    supported_currencies = Column(JSON, nullable=False)  # ["USD", "EUR", "GBP"]
    supported_countries = Column(JSON, nullable=False)
    
    # Features
    supports_deposits = Column(Boolean, default=True)
    supports_withdrawals = Column(Boolean, default=True)
    
    # Fees
    deposit_fee = Column(Float, default=0.0)
    withdrawal_fee = Column(Float, default=0.0)
    
    # Limits
    min_deposit = Column(Float, nullable=True)
    max_deposit = Column(Float, nullable=True)
    min_withdrawal = Column(Float, nullable=True)
    max_withdrawal = Column(Float, nullable=True)
    
    # Processing Time
    deposit_processing_time = Column(String(50), nullable=True)  # "instant", "1-3 days"
    withdrawal_processing_time = Column(String(50), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserFiatAccount(Base):
    __tablename__ = "user_fiat_accounts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    platform_id = Column(String, ForeignKey("fiat_platforms.id"), nullable=False)
    
    # Account Details
    account_number = Column(String(255), nullable=True)
    account_holder = Column(String(255), nullable=False)
    
    # Balance
    balance = Column(Float, default=0.0)
    currency = Column(String(3), nullable=False)  # USD, EUR, GBP
    
    # Verification
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

