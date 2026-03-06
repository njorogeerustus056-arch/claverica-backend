# notifications/signals.py - COMPLETELY FIXED VERSION WITH FULL DESTINATION DETAILS
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

                # Build comprehensive metadata with all destination details
                metadata = {
                    'admin_action_required': True,
                    'transfer_reference': instance.reference,
                    'amount': str(instance.amount),
                    'recipient': instance.recipient_name,
                    'action_url': f'/admin/compliance/transferrequest/{instance.id}/change/',
                    'destination_type': instance.destination_type,
                    'destination_details': instance.destination_details,  # Full JSON field
                }
                
                # Add specific fields based on destination type for easier viewing
                if instance.destination_type == 'mobile_wallet':
                    metadata['provider'] = instance.destination_details.get('provider', 'N/A')
                    metadata['phone_number'] = instance.destination_details.get('phone_number', 'N/A')
                    metadata['send_to'] = f"{metadata['provider']} - {metadata['phone_number']}"
                    
                elif instance.destination_type == 'bank':
                    metadata['bank_name'] = instance.destination_details.get('bank_name', 'N/A')
                    metadata['account_number'] = instance.destination_details.get('account_number', 'N/A')
                    metadata['account_type'] = instance.destination_details.get('account_type', 'N/A')
                    metadata['branch'] = instance.destination_details.get('branch', 'N/A')
                    metadata['send_to'] = f"{metadata['bank_name']} - {metadata['account_number']}"
                    
                elif instance.destination_type == 'crypto':
                    metadata['crypto_type'] = instance.destination_details.get('crypto_type', 'N/A')
                    metadata['crypto_address'] = instance.destination_details.get('crypto_address', 'N/A')
                    # Truncate address for display
                    address = metadata['crypto_address']
                    short_address = f"{address[:8]}..." if len(address) > 8 else address
                    metadata['send_to'] = f"{metadata['crypto_type']} - {short_address}"

                NotificationService.create_notification(
                    recipient=admin_account,
                    notification_type='ADMIN_TAC_REQUIRED',
                    title=f'New Transfer Requires TAC - ${instance.amount} to {instance.recipient_name}',
                    message=f'Transfer {instance.reference} requires TAC generation. Send to: {metadata.get("send_to", "Check details")}',
                    priority='HIGH',
                    metadata=metadata
                )
                
                logger.info(f"Admin notification created for transfer {instance.reference} to {instance.recipient_name}")
                
        elif instance.status == 'tac_sent':
            # Notification to client when TAC is sent
            NotificationService.create_notification(
                recipient=instance.account,
                notification_type='TAC_SENT',
                title='TAC Sent to Your Email',
                message=f'Authorization code sent for transfer {instance.reference} to {instance.recipient_name}',
                priority='HIGH',
                metadata={
                    'transfer_reference': instance.reference,
                    'amount': str(instance.amount),
                    'recipient': instance.recipient_name,
                    'expires_at': instance.tac_expires_at.isoformat() if instance.tac_expires_at else None,
                    'destination_type': instance.destination_type,
                    'destination_details': instance.destination_details,
                }
            )
            
        elif instance.status == 'tac_verified':
            # Notification when client verifies TAC
            NotificationService.create_notification(
                recipient=instance.account,
                notification_type='TAC_VERIFIED',
                title='Transfer Authorized',
                message=f'Transfer ${instance.amount} to {instance.recipient_name} authorized and ready for processing',
                priority='MEDIUM',
                metadata={
                    'transfer_reference': instance.reference,
                    'amount': str(instance.amount),
                    'recipient': instance.recipient_name,
                    'destination_type': instance.destination_type,
                }
            )
            
        elif instance.status == 'completed':
            # Notification when transfer is completed
            NotificationService.create_notification(
                recipient=instance.account,
                notification_type='TRANSFER_COMPLETED',
                title='Transfer Completed',
                message=f'Transfer of ${instance.amount} to {instance.recipient_name} completed successfully',
                priority='MEDIUM',
                metadata={
                    'transfer_reference': instance.reference,
                    'amount': str(instance.amount),
                    'recipient': instance.recipient_name,
                    'completion_date': timezone.now().isoformat(),
                    'destination_type': instance.destination_type,
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
            # Create default preferences for new account
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