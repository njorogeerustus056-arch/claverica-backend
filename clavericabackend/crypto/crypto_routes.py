from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import random
import hashlib

from database import get_db
from crypto_models import (
    CryptoAsset, CryptoWallet, CryptoTransaction,
    FiatPlatform, UserFiatAccount,
    TransactionType, TransactionStatus, WalletType
)

router = APIRouter(prefix="/api/crypto", tags=["crypto"])

class TransactionCreate(BaseModel):
    user_id: str
    asset_symbol: str
    transaction_type: str
    amount: float
    to_address: Optional[str] = None
    from_address: Optional[str] = None
    description: Optional[str] = None

class FiatAccountCreate(BaseModel):
    user_id: str
    platform_name: str
    account_holder: str
    account_number: Optional[str] = None
    currency: str

def simulate_price_update(asset: CryptoAsset) -> float:
    change = random.uniform(-0.02, 0.02)
    new_price = asset.current_price_usd * (1 + change)
    return round(new_price, 2)

def calculate_balance_usd(balance: float, price: float) -> float:
    return round(balance * price, 2)

@router.get("/assets")
async def get_all_assets(user_id: str = Query(...), db: Session = Depends(get_db)):
    try:
        assets = db.query(CryptoAsset).filter(CryptoAsset.is_active == True).all()
        result = []
        for asset in assets:
            wallet = db.query(CryptoWallet).filter(
                CryptoWallet.user_id == user_id,
                CryptoWallet.asset_id == asset.id,
                CryptoWallet.is_active == True
            ).first()
            
            current_price = simulate_price_update(asset)
            balance = wallet.balance if wallet else 0.0
            balance_usd = calculate_balance_usd(balance, current_price)
            
            result.append({
                "id": asset.id,
                "symbol": asset.symbol,
                "name": asset.name,
                "logo": asset.logo,
                "current_price_usd": current_price,
                "change_24h": asset.change_24h,
                "change_7d": asset.change_7d,
                "market_cap": asset.market_cap,
                "volume_24h": asset.volume_24h,
                "balance": balance,
                "balance_usd": balance_usd,
                "is_tradable": asset.is_tradable
            })
        
        return {"success": True, "assets": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/wallets/{user_id}")
async def get_user_wallets(user_id: str, db: Session = Depends(get_db)):
    try:
        wallets = db.query(CryptoWallet).filter(
            CryptoWallet.user_id == user_id,
            CryptoWallet.is_active == True
        ).all()
        
        result = []
        total_portfolio_usd = 0.0
        
        for wallet in wallets:
            asset = db.query(CryptoAsset).filter(CryptoAsset.id == wallet.asset_id).first()
            if not asset:
                continue
            
            current_price = simulate_price_update(asset)
            balance_usd = calculate_balance_usd(wallet.balance, current_price)
            total_portfolio_usd += balance_usd
            
            result.append({
                "id": wallet.id,
                "asset_id": asset.id,
                "asset_symbol": asset.symbol,
                "asset_name": asset.name,
                "asset_logo": asset.logo,
                "balance": wallet.balance,
                "available_balance": wallet.available_balance,
                "locked_balance": wallet.locked_balance,
                "balance_usd": balance_usd,
                "current_price": current_price,
                "wallet_address": wallet.wallet_address,
                "wallet_type": wallet.wallet_type,
                "is_active": wallet.is_active,
                "created_at": wallet.created_at.isoformat()
            })
        
        return {
            "success": True,
            "wallets": result,
            "total_portfolio_usd": round(total_portfolio_usd, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/wallets/create")
async def create_wallet(user_id: str, asset_symbol: str, db: Session = Depends(get_db)):
    try:
        asset = db.query(CryptoAsset).filter(CryptoAsset.symbol == asset_symbol).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        existing = db.query(CryptoWallet).filter(
            CryptoWallet.user_id == user_id,
            CryptoWallet.asset_id == asset.id
        ).first()
        
        if existing:
            return {
                "success": True,
                "wallet_id": existing.id,
                "message": "Wallet already exists"
            }
        
        wallet_address = f"0x{hashlib.sha256(f'{user_id}{asset.symbol}{datetime.utcnow()}'.encode()).hexdigest()[:40]}"
        
        wallet = CryptoWallet(
            user_id=user_id,
            asset_id=asset.id,
            wallet_address=wallet_address,
            wallet_type=WalletType.HOT,
            balance=0.0,
            available_balance=0.0,
            locked_balance=0.0
        )
        
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
        
        return {
            "success": True,
            "wallet_id": wallet.id,
            "wallet_address": wallet.wallet_address,
            "message": "Wallet created successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transactions/{user_id}")
async def get_user_transactions(
    user_id: str,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    transaction_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    try:
        query = db.query(CryptoTransaction).filter(CryptoTransaction.user_id == user_id)
        
        if transaction_type:
            query = query.filter(CryptoTransaction.transaction_type == transaction_type)
        
        if status:
            query = query.filter(CryptoTransaction.status == status)
        
        total_count = query.count()
        transactions = query.order_by(desc(CryptoTransaction.created_at)).offset(offset).limit(limit).all()
        
        result = []
        for txn in transactions:
            asset = db.query(CryptoAsset).filter(CryptoAsset.id == txn.asset_id).first()
            
            result.append({
                "id": txn.id,
                "asset_symbol": asset.symbol if asset else "N/A",
                "asset_name": asset.name if asset else "N/A",
                "transaction_type": txn.transaction_type,
                "status": txn.status,
                "amount": txn.amount,
                "amount_usd": txn.amount_usd,
                "fee": txn.fee,
                "from_address": txn.from_address,
                "to_address": txn.to_address,
                "transaction_hash": txn.transaction_hash,
                "confirmations": txn.confirmations,
                "created_at": txn.created_at.isoformat(),
                "completed_at": txn.completed_at.isoformat() if txn.completed_at else None
            })
        
        return {
            "success": True,
            "transactions": result,
            "total_count": total_count,
            "offset": offset,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/transactions/create")
async def create_transaction(transaction: TransactionCreate, db: Session = Depends(get_db)):
    try:
        asset = db.query(CryptoAsset).filter(CryptoAsset.symbol == transaction.asset_symbol).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        wallet = db.query(CryptoWallet).filter(
            CryptoWallet.user_id == transaction.user_id,
            CryptoWallet.asset_id == asset.id
        ).first()
        
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        
        if transaction.transaction_type in ["send", "sell", "swap"]:
            if wallet.available_balance < transaction.amount:
                raise HTTPException(status_code=400, detail="Insufficient balance")
        
        tx_hash = f"0x{hashlib.sha256(f'{transaction.user_id}{asset.symbol}{datetime.utcnow()}{transaction.amount}'.encode()).hexdigest()}"
        amount_usd = calculate_balance_usd(transaction.amount, asset.current_price_usd)
        
        txn = CryptoTransaction(
            user_id=transaction.user_id,
            asset_id=asset.id,
            transaction_type=TransactionType[transaction.transaction_type.upper()],
            status=TransactionStatus.PENDING,
            from_wallet_id=wallet.id if transaction.transaction_type in ["send", "sell"] else None,
            to_wallet_id=wallet.id if transaction.transaction_type in ["receive", "buy"] else None,
            from_address=transaction.from_address or wallet.wallet_address,
            to_address=transaction.to_address,
            amount=transaction.amount,
            amount_usd=amount_usd,
            price_at_transaction=asset.current_price_usd,
            transaction_hash=tx_hash,
            description=transaction.description,
            confirmations=0,
            required_confirmations=6
        )
        
        db.add(txn)
        
        if transaction.transaction_type in ["send", "sell", "swap"]:
            wallet.available_balance -= transaction.amount
            wallet.locked_balance += transaction.amount
        elif transaction.transaction_type in ["receive", "buy"]:
            wallet.balance += transaction.amount
            wallet.available_balance += transaction.amount
        
        wallet.balance_usd = calculate_balance_usd(wallet.balance, asset.current_price_usd)
        wallet.last_transaction_at = datetime.utcnow()
        
        db.commit()
        db.refresh(txn)
        
        return {
            "success": True,
            "transaction_id": txn.id,
            "transaction_hash": txn.transaction_hash,
            "status": txn.status,
            "message": "Transaction created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fiat-platforms")
async def get_fiat_platforms(db: Session = Depends(get_db)):
    try:
        platforms = db.query(FiatPlatform).filter(FiatPlatform.is_active == True).all()
        result = []
        for platform in platforms:
            result.append({
                "id": platform.id,
                "name": platform.name,
                "logo": platform.logo,
                "platform_type": platform.platform_type,
                "supported_currencies": platform.supported_currencies,
                "supports_deposits": platform.supports_deposits,
                "supports_withdrawals": platform.supports_withdrawals,
                "deposit_fee": platform.deposit_fee,
                "withdrawal_fee": platform.withdrawal_fee
            })
        return {"success": True, "platforms": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/fiat-accounts/create")
async def create_fiat_account(account: FiatAccountCreate, db: Session = Depends(get_db)):
    try:
        platform = db.query(FiatPlatform).filter(FiatPlatform.name == account.platform_name).first()
        if not platform:
            raise HTTPException(status_code=404, detail="Platform not found")
        
        existing = db.query(UserFiatAccount).filter(
            UserFiatAccount.user_id == account.user_id,
            UserFiatAccount.platform_id == platform.id
        ).first()
        
        if existing:
            return {"success": True, "account_id": existing.id, "message": "Account already linked"}
        
        fiat_account = UserFiatAccount(
            user_id=account.user_id,
            platform_id=platform.id,
            account_holder=account.account_holder,
            account_number=account.account_number,
            currency=account.currency,
            balance=0.0,
            is_verified=False
        )
        
        db.add(fiat_account)
        db.commit()
        db.refresh(fiat_account)
        
        return {
            "success": True,
            "account_id": fiat_account.id,
            "message": "Fiat account linked successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fiat-accounts/{user_id}")
async def get_user_fiat_accounts(user_id: str, db: Session = Depends(get_db)):
    try:
        accounts = db.query(UserFiatAccount).filter(
            UserFiatAccount.user_id == user_id,
            UserFiatAccount.is_active == True
        ).all()
        
        result = []
        for account in accounts:
            platform = db.query(FiatPlatform).filter(FiatPlatform.id == account.platform_id).first()
            result.append({
                "id": account.id,
                "platform_name": platform.name if platform else "N/A",
                "platform_logo": platform.logo if platform else None,
                "platform_type": platform.platform_type if platform else "N/A",
                "account_holder": account.account_holder,
                "account_number": account.account_number,
                "balance": account.balance,
                "currency": account.currency,
                "is_verified": account.is_verified,
                "created_at": account.created_at.isoformat()
            })
        return {"success": True, "accounts": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
