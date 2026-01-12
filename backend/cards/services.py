"""
cards/services.py - Business logic for cards (FIXED VERSION)
"""

import random
from datetime import datetime, timedelta
from decimal import Decimal
from django.db import transaction
from django.contrib.auth import get_user_model
from .models import Card, CardTransaction, CardStatus  # FIXED: CardTransaction instead of Transaction
from .exceptions import CardException

User = get_user_model()


class CardService:
    """Service for card-related operations"""
    
    @staticmethod
    def generate_card_details():
        """Generate card details"""
        return {
            'card_number': ''.join([str(random.randint(0, 9)) for _ in range(16)]),
            'cvv': ''.join([str(random.randint(0, 9)) for _ in range(3)]),
            'expiry_date': (datetime.now() + timedelta(days=1825)).strftime("%m/%y")
        }
    
    @staticmethod
    def create_card(user, card_data):
        """Create a new card for user"""
        details = CardService.generate_card_details()
        
        # Check if this should be primary card
        is_primary = not Card.objects.filter(user=user).exists()
        
        card = Card.objects.create(
            user=user,
            card_type=card_data.get('card_type'),
            card_number=details['card_number'],
            last_four=details['card_number'][-4:],
            cvv=details['cvv'],
            expiry_date=details['expiry_date'],
            cardholder_name=card_data.get('cardholder_name'),
            spending_limit=card_data.get('spending_limit', Decimal('5000.00')),
            color_scheme=card_data.get('color_scheme', 'from-indigo-500 via-purple-500 to-pink-500'),
            is_primary=is_primary,
            status=CardStatus.ACTIVE
        )
        
        return card
    
    @staticmethod
    @transaction.atomic
    def top_up_card(user, card_id, amount):
        """Top up a card from user's account"""
        card = Card.objects.select_for_update().get(id=card_id, user=user)
        
        # Get user's account
        try:
            from payments.models import Account
            account = Account.objects.select_for_update().filter(
                user=user,
                is_active=True
            ).first()
            
            if not account:
                raise CardException("No active account found")
            
            if account.balance < amount:
                raise CardException("Insufficient account balance")
            
            # Perform transfer
            account.balance -= amount
            account.save()
            
        except ImportError:
            raise CardException("Account management not available")
        
        # Update card balance
        card.balance += amount
        card.save()
        
        # Create transaction record
        transaction_record = CardTransaction.objects.create(  # FIXED: CardTransaction instead of Transaction
            user=user,
            card=card,
            amount=amount,
            merchant='Card Top-up',
            category='transfer',
            transaction_type='credit',
            status='completed',
            description=f'Top-up to card ending in {card.last_four}'
        )
        
        return {
            'card': card,
            'account': account,
            'transaction': transaction_record
        }
    
    @staticmethod
    def freeze_card(user, card_id):
        """Freeze a card"""
        card = Card.objects.get(id=card_id, user=user)
        card.status = CardStatus.FROZEN
        card.save()
        return card
    
    @staticmethod
    def unfreeze_card(user, card_id):
        """Unfreeze a card"""
        card = Card.objects.get(id=card_id, user=user)
        card.status = CardStatus.ACTIVE
        card.save()
        return card
    
    @staticmethod
    def set_primary_card(user, card_id):
        """Set a card as primary"""
        with transaction.atomic():
            # Remove primary from other cards
            Card.objects.filter(user=user, is_primary=True).update(is_primary=False)
            
            # Set new primary
            card = Card.objects.get(id=card_id, user=user)
            card.is_primary = True
            card.save()
        
        return card


class TransactionService:
    """Service for transaction-related operations"""
    
    @staticmethod
    def create_transaction(user, transaction_data):
        """Create a new transaction"""
        transaction = CardTransaction.objects.create(  # FIXED: CardTransaction instead of Transaction
            user=user,
            **transaction_data
        )
        return transaction
    
    @staticmethod
    def get_user_transactions(user, limit=50):
        """Get transactions for a user"""
        return CardTransaction.objects.filter(user=user).order_by('-created_at')[:limit]  # FIXED
    
    @staticmethod
    def get_card_transactions(card_id, user):
        """Get transactions for a specific card"""
        return CardTransaction.objects.filter(card_id=card_id, user=user).order_by('-created_at')  # FIXED