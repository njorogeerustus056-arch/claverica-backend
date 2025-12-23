from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_user
import random
from datetime import datetime, timedelta

router = APIRouter()

def generate_card_number():
    """Generate a 16-digit card number"""
    return ''.join([str(random.randint(0, 9)) for _ in range(16)])

def generate_cvv():
    """Generate a 3-digit CVV"""
    return ''.join([str(random.randint(0, 9)) for _ in range(3)])

def generate_expiry_date():
    """Generate expiry date (5 years from now)"""
    future_date = datetime.now() + timedelta(days=1825)
    return future_date.strftime("%m/%y")

@router.post("/", response_model=schemas.Card)
async def create_card(
    card: schemas.CardCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Generate card details
    card_number = generate_card_number()
    cvv = generate_cvv()
    expiry_date = generate_expiry_date()
    
    # Check if this should be primary card
    existing_cards = db.query(models.Card).filter(
        models.Card.user_id == current_user.id
    ).count()
    
    is_primary = existing_cards == 0
    
    # Create card
    db_card = models.Card(
        user_id=current_user.id,
        card_type=card.card_type,
        card_number=card_number,
        last_four=card_number[-4:],
        cvv=cvv,
        expiry_date=expiry_date,
        cardholder_name=card.cardholder_name,
        spending_limit=card.spending_limit,
        color_scheme=card.color_scheme,
        is_primary=is_primary,
        balance=0.0,
        status=models.CardStatus.ACTIVE
    )
    
    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    
    return db_card

@router.get("/", response_model=List[schemas.Card])
async def get_cards(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cards = db.query(models.Card).filter(
        models.Card.user_id == current_user.id
    ).order_by(models.Card.is_primary.desc(), models.Card.created_at.desc()).all()
    
    return cards

@router.get("/{card_id}", response_model=schemas.Card)
async def get_card(
    card_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    card = db.query(models.Card).filter(
        models.Card.id == card_id,
        models.Card.user_id == current_user.id
    ).first()
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    return card

@router.patch("/{card_id}", response_model=schemas.Card)
async def update_card(
    card_id: int,
    card_update: schemas.CardUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    card = db.query(models.Card).filter(
        models.Card.id == card_id,
        models.Card.user_id == current_user.id
    ).first()
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    # Update fields
    if card_update.spending_limit is not None:
        card.spending_limit = card_update.spending_limit
    
    if card_update.status is not None:
        card.status = card_update.status
    
    if card_update.is_primary is not None:
        if card_update.is_primary:
            # Remove primary from other cards
            db.query(models.Card).filter(
                models.Card.user_id == current_user.id,
                models.Card.id != card_id
            ).update({"is_primary": False})
        
        card.is_primary = card_update.is_primary
    
    db.commit()
    db.refresh(card)
    
    return card

@router.delete("/{card_id}")
async def delete_card(
    card_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    card = db.query(models.Card).filter(
        models.Card.id == card_id,
        models.Card.user_id == current_user.id
    ).first()
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    db.delete(card)
    db.commit()
    
    return {"message": "Card deleted successfully"}

@router.post("/{card_id}/freeze")
async def freeze_card(
    card_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    card = db.query(models.Card).filter(
        models.Card.id == card_id,
        models.Card.user_id == current_user.id
    ).first()
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    card.status = models.CardStatus.FROZEN
    db.commit()
    
    return {"message": "Card frozen successfully", "card": card}

@router.post("/{card_id}/unfreeze")
async def unfreeze_card(
    card_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    card = db.query(models.Card).filter(
        models.Card.id == card_id,
        models.Card.user_id == current_user.id
    ).first()
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    card.status = models.CardStatus.ACTIVE
    db.commit()
    
    return {"message": "Card unfrozen successfully", "card": card}

@router.post("/{card_id}/top-up")
async def top_up_card(
    card_id: int,
    amount: float,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    card = db.query(models.Card).filter(
        models.Card.id == card_id,
        models.Card.user_id == current_user.id
    ).first()
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    if current_user.balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient account balance")
    
    # Transfer from account to card
    current_user.balance -= amount
    card.balance += amount
    
    # Create transaction record
    transaction = models.Transaction(
        user_id=current_user.id,
        card_id=card_id,
        amount=amount,
        merchant="Card Top-up",
        category="transfer",
        transaction_type="credit",
        status="completed",
        description=f"Top-up to card ending in {card.last_four}"
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(card)
    
    return {
        "message": "Card topped up successfully",
        "card_balance": card.balance,
        "account_balance": current_user.balance
    }
