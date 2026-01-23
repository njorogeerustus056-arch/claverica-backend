"""
cards/signals.py - CORRECTED VERSION (FIXED)
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Card, CardTransaction  # FIXED: CardTransaction instead of Transaction
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@receiver(post_save, sender=CardTransaction)  # FIXED: CardTransaction instead of Transaction
def log_transaction_creation(sender, instance, created, **kwargs):
    """Log when a transaction is created"""
    if created:
        # Use instance.user.email instead of instance.user.username
        user_identifier = getattr(instance.user, 'email', 'Unknown User')
        logger.info(
            f"Transaction created: {instance.transaction_type} ${instance.amount} "
            f"at {instance.merchant} for user {user_identifier}"
        )


@receiver(pre_save, sender=Card)
def validate_card_expiry(sender, instance, **kwargs):
    """Validate card expiry date format"""
    from datetime import datetime
    
    try:
        # Check if expiry date is in MM/YY format
        if instance.expiry_date and len(instance.expiry_date) == 5:
            month, year = instance.expiry_date.split('/')
            month = int(month)
            year = int(year)
            
            if month < 1 or month > 12:
                raise ValueError("Invalid month")
            
            if year < 0 or year > 99:
                raise ValueError("Invalid year")
                
    except (ValueError, AttributeError, IndexError) as e:
        logger.error(f"Invalid expiry date for card {instance.id}: {e}")
        # Set a default expiry date if invalid
        from datetime import datetime, timedelta
        future_date = datetime.now() + timedelta(days=1825)
        instance.expiry_date = future_date.strftime("%m/%y")


@receiver(post_save, sender=User)
def create_default_card(sender, instance, created, **kwargs):
    """Create a default virtual card for new users"""
    if created:
        try:
            from .services import CardService
            
            # Check if user already has cards
            if Card.objects.filter(user=instance).exists():
                return
            
            # Create a default virtual card for new users
            card_data = {
                'card_type': 'virtual',
                'cardholder_name': f'{instance.first_name or ""} {instance.last_name or ""}'.strip() or instance.email,
                'spending_limit': '1000.00',
                'color_scheme': 'from-blue-500 to-green-500'
            }
            
            CardService.create_card(instance, card_data)
            
            logger.info(f"Created default card for user {instance.email}")
            
        except Exception as e:
            logger.error(f"Failed to create default card for user {instance.email}: {e}")