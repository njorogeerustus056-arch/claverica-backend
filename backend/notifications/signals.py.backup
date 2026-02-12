# notifications/signals.py - FINAL CORRECTED VERSION
import logging
import json
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

# Import all your app models
from accounts.models import Account
from payments.models import Payment
from transfers.models import Transfer, TAC
from kyc.models import KYCDocument
from compliance.models import TransferRequest  # ✅ CORRECT MODEL NAME

from .models import Notification, NotificationPreference, NotificationLog
from .services import NotificationService

logger = logging.getLogger(__name__)

# ========== COMPLIANCE SIGNALS ==========
@receiver(post_save, sender=TransferRequest)
def handle_compliance_notifications(sender, instance, created, **kwargs):
    """Create notifications for compliance events"""
    try:
        if created:
            # New transfer request - admin notification
            admin_accounts = Account.objects.filter(is_staff=True)
            if admin_accounts.exists():
                admin_account = admin_accounts.first()

                NotificationService.create_notification(
                    account=admin_account,
                    notification_type='ADMIN_TAC_REQUIRED',
                    title='New Transfer Requires TAC',
                    message=f'Transfer {instance.reference} for ${instance.amount:,.2f} requires TAC generation',
                    priority='HIGH',
                    metadata={
                        'admin_action_required': True,
                        'transfer_reference': instance.reference,
                        'amount': str(instance.amount),
                        'recipient': instance.recipient_name,
                        'action_url': f'/admin/compliance/transferrequest/{instance.id}/change/'
                    }
                )

            logger.info(f"Created compliance notification for transfer {instance.reference}")

        elif instance.status == 'tac_generated' and instance.tac_code:  # ✅ KEEP: TransferRequest has tac_code field
            # TAC generated - admin notification
            admin_accounts = Account.objects.filter(is_staff=True)
            if admin_accounts.exists():
                admin_account = admin_accounts.first()

                NotificationService.create_notification(
                    account=admin_account,
                    notification_type='ADMIN_TAC_GENERATED',
                    title='TAC Generated',
                    message=f'TAC {instance.tac_code} generated for transfer {instance.reference}',  # ✅ KEEP: tac_code
                    priority='MEDIUM',
                    metadata={
                        'admin_action_required': True,
                        'transfer_reference': instance.reference,
                        'tac_code': instance.tac_code,  # ✅ KEEP: tac_code
                        'action_url': f'/admin/compliance/transferrequest/{instance.id}/change/'
                    }
                )

        elif instance.status == 'tac_sent':
            # TAC sent to client - client notification
            NotificationService.create_notification(
                account=instance.account,  # This is Account object
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
            # TAC verified - client notification
            NotificationService.create_notification(
                account=instance.account,  # This is Account object
                notification_type='TAC_VERIFIED',
                title='Transfer Authorized',
                message=f'Transfer {instance.reference} authorized and ready for processing',
                priority='MEDIUM',
                metadata={
                    'transfer_reference': instance.reference,
                    'amount': str(instance.amount)
                }
            )

            # Admin notification for settlement
            admin_accounts = Account.objects.filter(is_staff=True)
            if admin_accounts.exists():
                admin_account = admin_accounts.first()

                NotificationService.create_notification(
                    account=admin_account,
                    notification_type='ADMIN_SETTLEMENT_REQUIRED',
                    title='Settlement Required',
                    message=f'Transfer {instance.reference} ready for external bank transfer',
                    priority='HIGH',
                    metadata={
                        'admin_action_required': True,
                        'transfer_reference': instance.reference,
                        'amount': str(instance.amount),
                        'recipient_account': json.loads(instance.destination_details).get('account_number', 'N/A') if instance.destination_details else 'N/A',
                        'action_url': f'/admin/compliance/transferrequest/{instance.id}/change/'
                    }
                )

        elif instance.status == 'pending_settlement':
            # Ready for manual bank transfer - admin notification
            admin_accounts = Account.objects.filter(is_staff=True)
            if admin_accounts.exists():
                admin_account = admin_accounts.first()

                NotificationService.create_notification(
                    account=admin_account,
                    notification_type='ADMIN_SETTLEMENT_REQUIRED',
                    title='Ready for Manual Transfer',
                    message=f'Transfer {instance.reference} awaiting external bank transfer',
                    priority='HIGH',
                    metadata={
                        'admin_action_required': True,
                        'transfer_reference': instance.reference,
                        'amount': str(instance.amount)
                    }
                )

        elif instance.status == 'completed':
            # Transfer completed - client notification
            NotificationService.create_notification(
                account=instance.account,  # This is Account object
                notification_type='TRANSFER_COMPLETED',
                title='Transfer Completed',
                message=f'Transfer of ${instance.amount:,.2f} to {instance.recipient_name} completed',
                priority='MEDIUM',
                metadata={
                    'transfer_reference': instance.reference,
                    'amount': str(instance.amount),
                    'recipient': instance.recipient_name,
                    'completion_date': timezone.now().isoformat()
                }
            )

        elif instance.status == 'kyc_required':
            # KYC required for transfer - client notification
            NotificationService.create_notification(
                account=instance.account,  # This is Account object
                notification_type='KYC_SUBMITTED',
                title='KYC Verification Required',
                message=f'Transfer requires KYC verification. Please submit documents.',
                priority='HIGH',
                metadata={
                    'transfer_reference': instance.reference,
                    'amount': str(instance.amount),
                    'threshold': '1500.00',
                    'redirect_url': '/kyc/submit/'
                }
            )

    except Exception as e:
        logger.error(f"Error handling compliance notification: {e}")

# ========== ACCOUNT SIGNALS ==========
@receiver(post_save, sender=Account)
def handle_account_notifications(sender, instance, created, **kwargs):
    """Create notifications for account events"""
    try:
        if created:
            # Create default preferences for new account
            NotificationPreference.objects.get_or_create(account=instance)

            # Notification for account creation
            NotificationService.create_notification(
                account=instance,
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

        elif getattr(instance, 'is_account_verified', False) and not getattr(instance, '_is_account_verified_previous', False):
            # Account verified notification
            NotificationService.create_notification(
                account=instance,
                notification_type='ACCOUNT_VERIFIED',
                title='Account Verified',
                message='Your account has been successfully verified!',
                priority='MEDIUM',
                metadata={
                    'account_number': instance.account_number,
                    'verification_date': timezone.now().isoformat()
                }
            )

    except Exception as e:
        logger.error(f"Error handling account notification: {e}")

# ========== PAYMENT SIGNALS ==========
@receiver(post_save, sender=Payment)
def handle_payment_notification(sender, instance, created, **kwargs):
    """Create notifications for payment events"""
    try:
        if instance.status == 'completed':
            # Use the service method
            NotificationService.send_payment_received_notification(instance)

    except Exception as e:
        logger.error(f"Error handling payment notification: {e}")

# ========== TRANSFER SIGNALS ==========
@receiver(post_save, sender=Transfer)
def handle_transfer_notification(sender, instance, created, **kwargs):
    """Create notifications for transfer events"""
    try:
        if created:
            # New transfer initiated - This will call the fixed NotificationService.send_transfer_notification
            NotificationService.send_transfer_notification(instance)
    except Exception as e:
        logger.error(f"Error handling transfer notification: {e}")

# ========== TAC SIGNALS ==========
@receiver(post_save, sender=TAC)
def handle_tac_notification(sender, instance, created, **kwargs):
    """Create notifications for TAC events"""
    try:
        if created and instance.code:  # ✅ CORRECT: TAC model has 'code' field
            NotificationService.send_tac_notification(instance)
    except Exception as e:
        logger.error(f"Error handling TAC notification: {e}")

# ========== KYC SIGNALS ==========
@receiver(post_save, sender=KYCDocument)
def handle_kyc_notifications(sender, instance, created, **kwargs):
    """Create notifications for KYC events"""
    try:
        if created:
            NotificationService.send_kyc_notification(instance)
    except Exception as e:
        logger.error(f"Error handling KYC notification: {e}")

# ========== HELPER FUNCTIONS ==========
def send_payment_email(payment):
    """Send payment received email"""
    try:
        subject = f'Payment Received - {payment.payment_code}'
        message = f"""
        Payment Confirmed: {payment.payment_code}

        You have received ${payment.amount:,.2f} from {payment.sender}
        on {payment.created_at.strftime("%d/%m/%Y")} at {payment.created_at.strftime("%I:%M %p")}

        New Account Balance: ${payment.balance_after:,.2f}

        Reference: {payment.reference}

        Thank you for using Claverica.
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[payment.account.email],
            fail_silently=False,
        )

        # Log email sent
        payment_notification = Notification.objects.filter(
            recipient=payment.account,
            notification_type='PAYMENT_RECEIVED'
        ).first()

        if payment_notification:
            NotificationLog.objects.create(
                notification=payment_notification,
                action='EMAIL_SENT',
                channel='EMAIL',
                details=f'Payment email sent to {payment.account.email}'
            )

    except Exception as e:
        logger.error(f"Error sending payment email: {e}")
        payment_notification = Notification.objects.filter(
            recipient=payment.account,
            notification_type='PAYMENT_RECEIVED'
        ).first()

        if payment_notification:
            NotificationLog.objects.create(
                notification=payment_notification,
                action='EMAIL_FAILED',
                channel='EMAIL',
                details=f'Failed to send email: {str(e)}'
            )