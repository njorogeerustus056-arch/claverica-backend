# users/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import UserProfile, UserSettings
import logging

logger = logging.getLogger(__name__)

User = settings.AUTH_USER_MODEL


@receiver(post_save, sender=User)
def create_user_profile_settings(sender, instance, created, **kwargs):
    """
    Automatically create UserProfile and UserSettings when a new User is created.
    This ensures every Account has a profile immediately.
    """
    if created:
        try:
            # Create UserProfile with default values
            UserProfile.objects.create(
                account=instance,
                subscription_tier='basic',
                avatar_color='#3B82F6'
            )
            
            # Create UserSettings with default values
            UserSettings.objects.create(
                account=instance,
                email_notifications=True,
                push_notifications=True
            )
            
            logger.info(f"✅ Created profile and settings for user {instance.id} ({instance.email})")
            
        except Exception as e:
            logger.error(f"⚠ Error creating profile/settings for user {instance.id}: {e}")
            # Don't raise exception, just log it


@receiver(post_save, sender=User)
def ensure_profile_settings_exist(sender, instance, **kwargs):
    """
    Ensure UserProfile and UserSettings exist for all users.
    This is a safety net in case signals didn't fire.
    """
    try:
        # Ensure profile exists
        if not hasattr(instance, 'user_profile'):
            UserProfile.objects.create(
                account=instance,
                subscription_tier='basic',
                avatar_color='#3B82F6'
            )
            logger.info(f"✅ Created missing profile for user {instance.id}")
    except Exception as e:
        logger.error(f"⚠ Error ensuring profile for user {instance.id}: {e}")
    
    try:
        # Ensure settings exist
        if not hasattr(instance, 'user_settings'):
            UserSettings.objects.create(account=instance)
            logger.info(f"✅ Created missing settings for user {instance.id}")
    except Exception as e:
        logger.error(f"⚠ Error ensuring settings for user {instance.id}: {e}")