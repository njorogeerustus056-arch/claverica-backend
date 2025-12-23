# notifications/signals.py
"""
Signal handlers for automatic notification creation and Pusher integration
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import NotificationPreference, Notification
from .pusher_client import trigger_notification

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
        NotificationPreference.objects.get_or_create(user=instance)


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
                "title": instance.title,
                "message": instance.message,
                "notification_type": instance.notification_type,
                "priority": instance.priority,
                "metadata": instance.metadata,
                "created_at": instance.created_at.isoformat()
            }
        )


# ==============================
# Example: Auto-send notifications from other apps
# ==============================
# Uncomment and customize based on your actual models

# from payments.models import Transaction, Card

# @receiver(post_save, sender=Transaction)
# def notify_transaction_status(sender, instance, created, **kwargs):
#     if instance.status in ['completed', 'failed']:
#         send_transaction_notification(user=instance.account, transaction=instance)

# @receiver(post_save, sender=Card)
# def notify_card_update(sender, instance, created, **kwargs):
#     if created:
#         send_card_notification(user=instance.account, card=instance, action='issued')
#     elif instance.status == 'blocked':
#         send_card_notification(user=instance.account, card=instance, action='blocked')

# @receiver(post_save, sender='kyc.KYCRecord')  # example KYC model
# def notify_kyc_update(sender, instance, created, **kwargs):
#     if instance.status in ['approved', 'rejected']:
#         send_kyc_notification(user=instance.user, status=instance.status, details={'kyc_id': instance.id})
