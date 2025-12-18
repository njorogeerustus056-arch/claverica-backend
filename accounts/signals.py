# accounts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Account

# Remove Profile-related signals entirely
# Add any Account-specific logic here if needed

@receiver(post_save, sender=Account)
def account_post_save(sender, instance, created, **kwargs):
    """
    Placeholder signal for Account post-save.
    Add any post-save logic for Account here.
    """
    if created:
        # Example: you could automatically create related objects here if needed
        pass
