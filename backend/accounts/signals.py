# accounts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Account

@receiver(post_save, sender=Account)
def account_post_save(sender, instance, created, **kwargs):
    """
    Signal for Account post-save.
    Profile and settings are now created in the AccountManager.
    """
    if created:
        # Additional initialization can go here
        pass