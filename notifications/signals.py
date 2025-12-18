# notifications/signals.py
"""
Signal handlers for automatic notification creation
"""

from django.db.models.signals import post_save
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
    Automatically create default notification preferences for new users.
    """
    if created:
        NotificationPreference.objects.get_or_create(user=instance)


# ==============================
# Example: Auto-send notifications
# ==============================
# These are templates to hook notifications to events in other apps.
# Uncomment and modify based on your actual models.

# from payments.models import Transaction, Card

# @receiver(post_save, sender=Transaction)
# def notify_transaction_status(sender, instance, created, **kwargs):
#     """
#     Send notification when a transaction is completed or failed.
#     """
#     if instance.status in ['completed', 'failed']:
#         send_transaction_notification(user=instance.account.user, transaction=instance)


# @receiver(post_save, sender=Card)
# def notify_card_update(sender, instance, created, **kwargs):
#     """
#     Send notification when a card is issued or blocked.
#     """
#     if created:
#         send_card_notification(user=instance.account.user, card=instance, action='issued')
#     elif instance.status == 'blocked':
#         send_card_notification(user=instance.account.user, card=instance, action='blocked')


# @receiver(post_save, sender='kyc.KYCRecord')  # example KYC app model
# def notify_kyc_update(sender, instance, created, **kwargs):
#     """
#     Send notification when KYC is approved or rejected.
#     """
#     if instance.status in ['approved', 'rejected']:
#         send_kyc_notification(user=instance.user, kyc_record=instance)
