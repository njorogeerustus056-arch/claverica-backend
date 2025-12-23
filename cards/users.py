from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter()

@router.get("/me", response_model=schemas.User)
async def get_current_user_info(
    current_user: models.User = Depends(get_current_user)
):
    return current_user

@router.get("/balance")
async def get_balance(
    current_user: models.User = Depends(get_current_user)
):
    return {
        "balance": current_user.balance,
        "account_number": current_user.account_number,
        "currency": "USD"
    }

@router.post("/balance/add")
async def add_balance(
    amount: float,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    current_user.balance += amount
    db.commit()
    db.refresh(current_user)
    
    return {
        "message": "Balance added successfully",
        "new_balance": current_user.balance
    }

@router.get("/transactions", response_model=List[schemas.Transaction])
async def get_transactions(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    transactions = db.query(models.Transaction).filter(
        models.Transaction.user_id == current_user.id
    ).order_by(models.Transaction.created_at.desc()).limit(50).all()
    
    return transactions
