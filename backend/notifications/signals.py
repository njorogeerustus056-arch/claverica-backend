# notifications/signals.py - COMPLETELY FIXED VERSION
import logging
import json
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from accounts.models import Account
from payments.models import Payment
from transfers.models import Transfer, TAC
from kyc.models import KYCDocument
from compliance.models import TransferRequest

from .models import Notification, NotificationPreference, NotificationLog
from .services import NotificationService

logger = logging.getLogger(__name__)

# ========== COMPLIANCE SIGNALS ==========
@receiver(post_save, sender=TransferRequest)
def handle_compliance_notifications(sender, instance, created, **kwargs):
    '''Create notifications for compliance events'''
    try:
        if created:
            admin_accounts = Account.objects.filter(is_staff=True)
            if admin_accounts.exists():
                admin_account = admin_accounts.first()

                NotificationService.create_notification(
                    recipient=admin_account,
                    notification_type='ADMIN_TAC_REQUIRED',
                    title='New Transfer Requires TAC',
                    message=f'Transfer {instance.reference} for  requires TAC generation',
                    priority='HIGH',
                    metadata={
                        'admin_action_required': True,
                        'transfer_reference': instance.reference,
                        'amount': str(instance.amount),
                        'recipient': instance.recipient_name,
                        'action_url': f'/admin/compliance/transferrequest/{instance.id}/change/'
                    }
                )
        elif instance.status == 'tac_sent':
            NotificationService.create_notification(
                recipient=instance.account,
                notification_type='TAC_SENT',
                title='TAC Sent to Your Email',
                message=f'Authorization code sent for transfer {instance.reference}',
                priority='HIGH',
                metadata={
                    'transfer_reference': instance.reference,
                    'amount': str(instance.amount),
                    'expires_at': instance.tac_expires_at.isoformat() if instance.tac_expires_at else None
                }
            )
        elif instance.status == 'tac_verified':
            NotificationService.create_notification(
                recipient=instance.account,
                notification_type='TAC_VERIFIED',
                title='Transfer Authorized',
                message=f'Transfer {instance.reference} authorized and ready for processing',
                priority='MEDIUM',
                metadata={
                    'transfer_reference': instance.reference,
                    'amount': str(instance.amount)
                }
            )
        elif instance.status == 'completed':
            NotificationService.create_notification(
                recipient=instance.account,
                notification_type='TRANSFER_COMPLETED',
                title='Transfer Completed',
                message=f'Transfer of  to {instance.recipient_name} completed',
                priority='MEDIUM',
                metadata={
                    'transfer_reference': instance.reference,
                    'amount': str(instance.amount),
                    'recipient': instance.recipient_name,
                    'completion_date': timezone.now().isoformat()
                }
            )
    except Exception as e:
        logger.error(f"Error handling compliance notification: {e}")

# ========== ACCOUNT SIGNALS ==========
@receiver(post_save, sender=Account)
def handle_account_notifications(sender, instance, created, **kwargs):
    '''Create notifications for account events'''
    try:
        if created:
            # Create default preferences for new account - FIXED: 'account' not 'recipient'
            NotificationPreference.objects.get_or_create(account=instance)

            NotificationService.create_notification(
                recipient=instance,
                notification_type='ACCOUNT_CREATED',
                title='New Account Created',
                message=f'Welcome to Claverica! Your account {instance.account_number} has been created.',
                priority='MEDIUM',
                metadata={
                    'account_number': instance.account_number,
                    'email': instance.email,
                    'admin_action_required': False
                }
            )
            logger.info(f"Created account notification for {instance.account_number}")
    except Exception as e:
        logger.error(f"Error handling account notification: {e}")

@receiver(post_save, sender=Payment)
def handle_payment_notification(sender, instance, created, **kwargs):
    '''Create notifications for payment events'''
    try:
        if instance.status == 'completed':
            NotificationService.send_payment_received_notification(instance)
    except Exception as e:
        logger.error(f"Error handling payment notification: {e}")

# ========== TRANSFER SIGNALS ==========
@receiver(post_save, sender=Transfer)
def handle_transfer_notification(sender, instance, created, **kwargs):
    '''Create notifications for transfer events'''
    try:
        if created:
            NotificationService.send_transfer_notification(instance)
    except Exception as e:
        logger.error(f"Error handling transfer notification: {e}")

# ========== TAC SIGNALS ==========
@receiver(post_save, sender=TAC)
def handle_tac_notification(sender, instance, created, **kwargs):
    '''Create notifications for TAC events'''
    try:
        if created and instance.code:
            NotificationService.send_tac_notification(instance)
    except Exception as e:
        logger.error(f"Error handling TAC notification: {e}")

# ========== KYC SIGNALS ==========
@receiver(post_save, sender=KYCDocument)
def handle_kyc_notifications(sender, instance, created, **kwargs):
    '''Create notifications for KYC events'''
    try:
        if created:
            NotificationService.send_kyc_notification(instance)
    except Exception as e:
        logger.error(f"Error handling KYC notification: {e}")


