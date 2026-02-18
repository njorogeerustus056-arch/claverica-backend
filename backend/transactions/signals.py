"""
transactions/signals.py
Signals for auto-creating wallet when Account is created
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from accounts.models import Account
from .models import Wallet

@receiver(post_save, sender=Account)
def create_wallet_for_new_account(sender, instance, created, **kwargs):
    """
    Automatically create a Wallet when a new Account is created.
    This serves as a backup to the signal in users/signals.py
    """
    if created:
        try:
            print(f'\n[TRANSACTIONS SIGNAL] Creating wallet for {instance.email}')
            print(f'   Account#: {instance.account_number}')
            
            # Ensure account number exists
            if not instance.account_number:
                print(f'     No account number yet - skipping wallet creation')
                return
            
            # Check if wallet already exists
            wallet_exists = Wallet.objects.filter(account=instance).exists()
            if wallet_exists:
                print(f'    Wallet already exists')
                return
            
            # Create wallet
            wallet = Wallet.objects.create(
                account=instance,
                balance=0.00,
                currency='USD'
            )
            print(f'    Wallet created: {wallet.id}')
            print(f'   Balance: {wallet.balance} {wallet.currency}')
            
        except Exception as e:
            print(f'    Error creating wallet: {e}')
            import traceback
            traceback.print_exc()

@receiver(post_delete, sender=Account)
def delete_wallet_when_account_deleted(sender, instance, **kwargs):
    """
    Delete wallet when Account is deleted
    """
    try:
        Wallet.objects.filter(account=instance).delete()
        print(f'[TRANSACTIONS SIGNAL] Wallet deleted for account {instance.account_number}')
    except Wallet.DoesNotExist:
        pass
    except Exception as e:
        print(f'[TRANSACTIONS SIGNAL] Error deleting wallet: {e}')
