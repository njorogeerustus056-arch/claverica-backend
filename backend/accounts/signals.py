# accounts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def user_post_save(sender, instance, created, **kwargs):
    """
    Signal for User post-save.
    Note: Profile and settings are now created in users app.
    """
    if created:
        # Minimal initialization for authentication
        # User management (profile, settings) happens in users app
        pass