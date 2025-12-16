"""
Signal handlers for automatic notification creation
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import NotificationPreference
from .utils import (
    send_transaction_notification,
    send_card_notification,
    send_kyc_notification
)


@receiver(post_save, sender=User)
def create_notification_preferences(sender, instance, created, **kwargs):
    """
    Automatically create notification preferences for new users
    """
    if created:
        NotificationPreference.objects.get_or_create(user=instance)


# Example: Auto-send notifications when certain events happen
# Uncomment and modify based on your models

# @receiver(post_save, sender='payments.Transaction')
# def notify_transaction_status(sender, instance, created, **kwargs):
#     """
#     Send notification when transaction is created or updated
#     """
#     if instance.status in ['completed', 'failed']:
#         send_transaction_notification(instance.account.user, instance)


# @receiver(post_save, sender='payments.Card')
# def notify_card_update(sender, instance, created, **kwargs):
#     """
#     Send notification when card is created or status changes
#     """
#     if created:
#         send_card_notification(instance.account.user, instance, 'issued')
#     elif instance.status == 'blocked':
#         send_card_notification(instance.account.user, instance, 'blocked')
