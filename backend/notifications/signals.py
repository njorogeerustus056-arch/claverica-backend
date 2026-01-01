# notifications/signals.py
"""
Signal handlers for automatic notification creation and Pusher integration
"""
from django.db import IntegrityError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import NotificationPreference, Notification
from .pusher_client import trigger_notification  # ✅ Fixed: Use pusher_client module

# Reference the custom user model dynamically
UserModel = settings.AUTH_USER_MODEL

# -----------------------------
# User notification preferences
# -----------------------------
@receiver(post_save, sender=UserModel)
def create_notification_preferences(sender, instance, created, **kwargs):
    """
    Automatically create default notification preferences for new users.
    """
    if created:
        try:
            # Try to create notification preferences
            NotificationPreference.objects.create(user=instance)
            print(f"✅ Created notification preferences for user {instance.id}")
        except IntegrityError as e:
            # If foreign key constraint fails, log and continue
            print(f"⚠️ Could not create notification preferences for user {instance.id}: {e}")
            # Don't raise the error - let user creation succeed
            pass
        except Exception as e:
            # Catch any other errors
            print(f"⚠️ Error creating notification preferences: {e}")
            pass

# -----------------------------
# Real-time notification via Pusher
# -----------------------------
@receiver(post_save, sender=Notification)
def send_notification_pusher(sender, instance, created, **kwargs):
    """
    Trigger Pusher automatically when a new Notification is created.
    """
    if created:
        trigger_notification(
            user_id=instance.user.id,
            event="new_notification",
            data={
                "id": instance.id,
                "notification_id": str(instance.notification_id),
                "title": instance.title,
                "message": instance.message,
                "notification_type": instance.notification_type,
                "priority": instance.priority,
                "metadata": instance.metadata or {},
                "created_at": instance.created_at.isoformat(),
                "is_read": instance.is_read,
                "action_url": instance.action_url or "",
                "action_label": instance.action_label or "",
                "time_ago": instance.time_ago
            }
        )