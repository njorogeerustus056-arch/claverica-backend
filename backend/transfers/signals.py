"""
transfers/signals.py - Signal wallet deductions ONLY
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Transfer
from transactions.models import Wallet
from transactions.services import WalletService
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Transfer)
def deduct_wallet_on_verified_transfer(sender, instance, created, **kwargs):
    """
    When a transfer is verified (TAC verified), deduct from wallet
    This is the ONLY signal needed in transfers app
    """
    # Check if this is a status update to 'tac_verified'
    if not created and instance.status == 'tac_verified':
        try:
            # Get the previous state to avoid double deduction
            if hasattr(instance, '_original_status'):
                if instance._original_status == instance.status:
                    return
            
            print(f'\n[TRANSFERS SIGNAL] Deducting ${instance.amount} from wallet')
            print(f'   Account: {instance.account.account_number}')
            
            # Use Transactions app service to deduct funds
            new_balance = WalletService.debit_wallet(
                account_number=instance.account.account_number,
                amount=instance.amount,
                reference=instance.reference,
                description=f"Transfer to {instance.recipient_name}"
            )
            
            print(f'    Funds deducted. New balance: ${new_balance}')
            
            # Update transfer status to funds_deducted
            instance.status = 'funds_deducted'
            instance.save(update_fields=['status'])
            
        except Exception as e:
            print(f'    Error deducting funds: {e}')
            logger.error(f"Failed to deduct wallet for transfer {instance.reference}: {e}")

# Store original status on model init
from django.db.models.signals import post_init

@receiver(post_init, sender=Transfer)
def store_original_status(sender, instance, **kwargs):
    """Store original status to detect changes"""
    instance._original_status = instance.status
