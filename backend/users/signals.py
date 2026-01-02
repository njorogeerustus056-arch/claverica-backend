# users/signals.py - MAKE SURE THIS EXISTS
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import UserProfile, UserSettings

User = settings.AUTH_USER_MODEL


@receiver(post_save, sender=User)
def create_user_profile_settings(sender, instance, created, **kwargs):
    """
    Automatically create UserProfile and UserSettings when a new User is created.
    """
    if created:
        try:
            UserProfile.objects.create(account=instance)
            UserSettings.objects.create(account=instance)
            print(f"✅ Created profile and settings for user {instance.id}")
        except Exception as e:
            print(f"⚠ Error creating profile/settings for user {instance.id}: {e}")


@receiver(post_save, sender=User)
def save_user_profile_settings(sender, instance, **kwargs):
    """
    Ensure UserProfile and UserSettings exist for existing users.
    """
    try:
        instance.user_profile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(account=instance)
    except Exception as e:
        print(f"⚠ Error saving user profile for {instance.id}: {e}")
    
    try:
        instance.user_settings.save()
    except UserSettings.DoesNotExist:
        UserSettings.objects.create(account=instance)
    except Exception as e:
        print(f"⚠ Error saving user settings for {instance.id}: {e}")