# payments/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Account

User = get_user_model()

@receiver(post_save, sender=User)
def create_default_account(sender, instance, created, **kwargs):
    """
    Create a default checking account for new users
    """
    if created:
        Account.objects.create(
            user=instance,
            account_type='checking',
            currency='USD',
            balance=0.00,
            available_balance=0.00,
            is_verified=False,
            is_active=True
        )