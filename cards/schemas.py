from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class CardType(str, Enum):
    VIRTUAL = "virtual"
    PHYSICAL = "physical"

class CardStatus(str, Enum):
    ACTIVE = "active"
    FROZEN = "frozen"
    CANCELLED = "cancelled"

class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class User(UserBase):
    id: int
    account_number: str
    balance: float
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class CardBase(BaseModel):
    card_type: CardType
    cardholder_name: str
    spending_limit: Optional[float] = 5000.0
    color_scheme: Optional[str] = "from-indigo-500 via-purple-500 to-pink-500"

class CardCreate(CardBase):
    pass

class Card(CardBase):
    id: int
    user_id: int
    card_number: str
    last_four: str
    cvv: str
    expiry_date: str
    balance: float
    status: CardStatus
    is_primary: bool
    created_at: datetime

    class Config:
        from_attributes = True

class CardUpdate(BaseModel):
    spending_limit: Optional[float] = None
    status: Optional[CardStatus] = None
    is_primary: Optional[bool] = None

class TransactionBase(BaseModel):
    amount: float
    merchant: str
    category: Optional[str] = None
    transaction_type: str
    description: Optional[str] = None

class TransactionCreate(TransactionBase):
    card_id: Optional[int] = None

class Transaction(TransactionBase):
    id: int
    user_id: int
    card_id: Optional[int]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
