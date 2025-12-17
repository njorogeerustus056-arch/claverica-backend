from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base

class CardType(str, enum.Enum):
    VIRTUAL = "virtual"
    PHYSICAL = "physical"

class CardStatus(str, enum.Enum):
    ACTIVE = "active"
    FROZEN = "frozen"
    CANCELLED = "cancelled"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    account_number = Column(String, unique=True, index=True)
    balance = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cards = relationship("Card", back_populates="owner", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")

class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    card_type = Column(Enum(CardType), nullable=False)
    card_number = Column(String, unique=True, index=True, nullable=False)
    last_four = Column(String, nullable=False)
    cvv = Column(String, nullable=False)
    expiry_date = Column(String, nullable=False)
    cardholder_name = Column(String, nullable=False)
    balance = Column(Float, default=0.0)
    spending_limit = Column(Float, default=5000.0)
    status = Column(Enum(CardStatus), default=CardStatus.ACTIVE)
    color_scheme = Column(String, default="from-indigo-500 via-purple-500 to-pink-500")
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="cards")
    transactions = relationship("Transaction", back_populates="card", cascade="all, delete-orphan")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    card_id = Column(Integer, ForeignKey("cards.id"))
    amount = Column(Float, nullable=False)
    merchant = Column(String, nullable=False)
    category = Column(String)
    transaction_type = Column(String, nullable=False)  # credit, debit
    status = Column(String, default="completed")
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="transactions")
    card = relationship("Card", back_populates="transactions")
