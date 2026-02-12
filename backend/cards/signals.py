# backend/cards/signals.py - CORRECTED
"""
cards/signals.py - CORRECTED VERSION (FIXED)
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Card, CardTransaction
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

# ========== IMPORTANT FIX ==========
# Since your AUTH_USER_MODEL = 'accounts.Account', we need to import it
try:
    from accounts.models import Account
    USER_MODEL = Account
except ImportError:
    USER_MODEL = User  # Fallback
# ========== END FIX ==========

@receiver(post_save, sender=CardTransaction)
def log_transaction_creation(sender, instance, created, **kwargs):
    """Log when a transaction is created"""
    if created:
        user_identifier = getattr(instance.account, 'email', 'Unknown User')
        logger.info(
            f"Card transaction created: {instance.transaction_type} ${instance.amount} "
            f"at {instance.merchant} for user {user_identifier}"
        )


@receiver(pre_save, sender=Card)
def validate_card_expiry(sender, instance, **kwargs):
    """Validate card expiry date format"""
    from datetime import datetime

    try:
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
        from datetime import datetime, timedelta
        future_date = datetime.now() + timedelta(days=1825)
        instance.expiry_date = future_date.strftime("%m/%y")


# ========== FIXED: Use correct User model ==========
@receiver(post_save, sender=USER_MODEL)  # FIXED: Use USER_MODEL which is Account
def create_default_card(sender, instance, created, **kwargs):
    """Create a default virtual card for new users - FIXED"""
    if created:
        try:
            from .services import CardService

            # Get account (instance IS Account in your system)
            account = instance

            # Check if account already has cards
            if Card.objects.filter(account=account).exists():
                return

            # Create a default virtual card for new users
            card = CardService.create_card(
                account=account,
                card_type='virtual',
                is_primary=True,
                cardholder_name=f'{account.first_name or ""} {account.last_name or ""}'.strip() or account.email,
                color_scheme='blue-gradient'
            )

            logger.info(f"Created default card for account {account.email}")

        except Exception as e:
            logger.error(f"Failed to create default card for account {instance.email}: {e}")
