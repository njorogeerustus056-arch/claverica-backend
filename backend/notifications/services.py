"""
🎉 NOTIFICATION SERVICE - Financial System Integration
The communication spine for your digital banking ecosystem
"""

import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .models import Notification, NotificationLog, NotificationPreference
from accounts.models import Account
from transactions.models import Wallet, Transaction
from payments.models import Payment
from transfers.models import Transfer, TAC
from kyc.models import KYCDocument
from compliance.models import TransferRequest

logger = logging.getLogger(__name__)

class NotificationService:
    """Central notification service for financial workflows"""

    @staticmethod
    def create_notification(account, notification_type, title, message, priority='MEDIUM', metadata=None):
        """
        Create a notification for an account

        Args:
            account: Account object
            notification_type: Type of notification (PAYMENT_RECEIVED, etc.)
            title: Notification title
            message: Notification message
            priority: HIGH, MEDIUM, LOW
            metadata: Additional data as dict
        """
        try:
            notification = Notification.objects.create(
                recipient=account,  # ✅ CRITICAL: Using 'recipient' not 'account'
                notification_type=notification_type,
                title=title,
                message=message,
                priority=priority,
                metadata=metadata or {}
            )

            # Log the creation
            NotificationLog.objects.create(
                notification=notification,
                action='CREATED',
                channel='IN_APP',
                details=f'Notification created for {account.account_number}'
            )

            # Send email if enabled
            NotificationService.send_email_notification(notification)

            return notification

        except Exception as e:
            logger.error(f"❌ Error creating notification: {str(e)}")
            return None

    @staticmethod
    def send_payment_received_notification(payment_instance):
        """
        Send notification when payment is received
        """
        try:
            # Get account from payment instance
            account = payment_instance.account  # ✅ This should be Account object

            notification = NotificationService.create_notification(
                account=account,
                notification_type='PAYMENT_RECEIVED',
                title='💰 Payment Received',
                message=f'You received ${payment_instance.amount:.2f} from {payment_instance.sender}',
                priority='HIGH',
                metadata={
                    'amount': str(payment_instance.amount),
                    'sender': payment_instance.sender,
                    'reference': payment_instance.reference,
                    'payment_code': payment_instance.payment_code,
                    'transaction_type': 'credit',
                    'timestamp': timezone.now().isoformat(),
                    'new_balance': str(payment_instance.balance_after) if hasattr(payment_instance, 'balance_after') else 'N/A'
                }
            )

            # Also send admin notification
            NotificationService.send_admin_payment_notification(payment_instance)

            logger.info(f"✅ Payment notification created for {account.account_number}: ${payment_instance.amount}")
            return notification

        except Exception as e:
            logger.error(f"❌ Error sending payment notification: {str(e)}")
            return None

    @staticmethod
    def send_admin_payment_notification(payment_instance):
        """Send admin notification for payment processing"""
        try:
            # Find an admin account (first account with is_staff=True)
            admin_accounts = Account.objects.filter(is_staff=True)
            if admin_accounts.exists():
                admin_account = admin_accounts.first()

                NotificationService.create_notification(
                    account=admin_account,
                    notification_type='ADMIN_PAYMENT_PROCESSED',
                    title='📋 Payment Processed',
                    message=f'Payment of ${payment_instance.amount:.2f} processed for {payment_instance.account.account_number}',
                    priority='MEDIUM',
                    metadata={
                        'client_account': payment_instance.account.account_number,
                        'client_email': payment_instance.account.email,
                        'amount': str(payment_instance.amount),
                        'sender': payment_instance.sender,
                        'payment_code': payment_instance.payment_code,
                        'admin_action_required': False,
                        'processed_by': payment_instance.admin_user.username if payment_instance.admin_user else 'System'
                    }
                )

        except Exception as e:
            logger.error(f"⚠️ Error sending admin payment notification: {str(e)}")

    @staticmethod
    def send_transfer_notification(transfer_instance):
        """
        Send notification for transfer events
        """
        try:
            account = transfer_instance.account  # ✅ This should be Account object
            notification_type = 'TRANSFER_INITIATED'
            title = '🚀 Transfer Initiated'

            if hasattr(transfer_instance, 'status'):
                if transfer_instance.status == 'completed':
                    notification_type = 'TRANSFER_COMPLETED'
                    title = '✅ Transfer Completed'
                elif transfer_instance.status == 'failed':
                    notification_type = 'TRANSFER_FAILED'
                    title = '❌ Transfer Failed'

            # ✅ FIXED: Use recipient_name instead of beneficiary_name
            notification = NotificationService.create_notification(
                account=account,
                notification_type=notification_type,
                title=title,
                message=f'Transfer of ${transfer_instance.amount:.2f} to {transfer_instance.recipient_name}',
                priority='HIGH',
                metadata={
                    'amount': str(transfer_instance.amount),
                    'recipient_name': transfer_instance.recipient_name,  # ✅ FIXED
                    'recipient_account': transfer_instance.beneficiary_account if hasattr(transfer_instance, 'beneficiary_account') else 'N/A',
                    'status': transfer_instance.status if hasattr(transfer_instance, 'status') else 'pending',
                    'reference': transfer_instance.reference if hasattr(transfer_instance, 'reference') else 'N/A',
                    'timestamp': timezone.now().isoformat()
                }
            )

            return notification

        except Exception as e:
            logger.error(f"❌ Error sending transfer notification: {str(e)}")
            return None

    @staticmethod
    def send_tac_notification(tac_instance):
        """
        Send TAC notification
        """
        try:
            # ✅ FIXED: Get account from transfer, not from tac_instance directly
            account = tac_instance.transfer.account

            # ✅ FIXED: Use 'code' not 'tac_code'
            notification = NotificationService.create_notification(
                account=account,
                notification_type='TAC_SENT',
                title='🔐 Your TAC Code',
                message=f'Your TAC code is {tac_instance.code} for transfer authorization',
                priority='HIGH',
                metadata={
                    'tac_code': tac_instance.code,  # ✅ FIXED: Use 'code'
                    'purpose': 'transfer verification',
                    'expires_at': tac_instance.expires_at.isoformat() if tac_instance.expires_at else None,
                    'security_warning': 'Do not share this code with anyone',
                    'instructions': 'Enter this code in the verification form'
                }
            )

            return notification

        except Exception as e:
            logger.error(f"❌ Error sending TAC notification: {str(e)}")
            return None

    @staticmethod
    def send_kyc_notification(kyc_instance):
        """
        Send KYC notification
        """
        try:
            # ✅✅✅ FIXED: Get account from user (KYCDocument has 'user' not 'account')
            # Try to get account from user
            user = kyc_instance.user
            
            # Method 1: If user has account attribute
            if hasattr(user, 'account'):
                account = user.account
            # Method 2: Try to get account by email
            else:
                try:
                    account = Account.objects.get(email=user.email)
                except Account.DoesNotExist:
                    # Method 3: Try to get account by user relation
                    try:
                        account = Account.objects.get(user=user)
                    except Account.DoesNotExist:
                        # Method 4: Try to get first account with matching email
                        account = Account.objects.filter(email=user.email).first()
                        if not account:
                            logger.error(f"❌ Cannot find account for user {user.email}")
                            return None
            
            notification_type = 'KYC_SUBMITTED'
            title = '📤 KYC Submitted'

            if hasattr(kyc_instance, 'status'):
                if kyc_instance.status == 'approved':
                    notification_type = 'KYC_APPROVED'
                    title = '✅ KYC Approved'
                elif kyc_instance.status == 'rejected':
                    notification_type = 'KYC_REJECTED'
                    title = '❌ KYC Rejected'
                elif kyc_instance.status == 'under_review':
                    notification_type = 'KYC_UNDER_REVIEW'
                    title = '⏳ KYC Under Review'

            notification = NotificationService.create_notification(
                account=account,
                notification_type=notification_type,
                title=title,
                message=f'Your KYC documents have been {getattr(kyc_instance, "status", "submitted")}',
                priority='HIGH',
                metadata={
                    'kyc_id': str(kyc_instance.id),
                    'document_type': kyc_instance.document_type,
                    'status': getattr(kyc_instance, 'status', 'submitted'),
                    'rejection_reason': kyc_instance.rejection_reason if hasattr(kyc_instance, 'rejection_reason') else None,
                    'submitted_at': kyc_instance.submitted_at.isoformat() if hasattr(kyc_instance, 'submitted_at') else None,
                    'timestamp': timezone.now().isoformat()
                }
            )

            logger.info(f"✅ KYC notification sent for account {account.account_number}")
            return notification

        except Exception as e:
            logger.error(f"❌ Error sending KYC notification: {str(e)}")
            return None

    @staticmethod
    def send_email_notification(notification):
        """
        Send email for important notifications

        Args:
            notification: Notification object
        """
        try:
            # Check if email is enabled for this account
            try:
                # FIX: Use recipient (which is Account) to get preferences
                pref = NotificationPreference.objects.get(account=notification.recipient)
                if not pref.email_enabled:
                    return False

                # Check priority settings
                if notification.priority == 'HIGH' and not pref.email_high_priority:
                    return False
                elif notification.priority == 'MEDIUM' and not pref.email_medium_priority:
                    return False
                elif notification.priority == 'LOW' and not pref.email_low_priority:
                    return False

            except NotificationPreference.DoesNotExist:
                # No preference found, create default
                pref = NotificationPreference.objects.create(account=notification.recipient)
                if not pref.email_enabled:
                    return False

            # Prepare email
            subject = f"Claverica: {notification.title}"

            # Simple email template
            message = f"""
            {notification.title}

            {notification.message}

            Account: {notification.recipient.account_number}
            Time: {notification.created_at.strftime('%Y-%m-%d %H:%M')}

            Notification Type: {notification.get_notification_type_display()}

            ---
            This is an automated notification from Claverica Financial System.
            Do not reply to this email.
            """

            # Send email
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notification.recipient.email],
                fail_silently=True,
            )

            # Log email delivery
            NotificationLog.objects.create(
                notification=notification,
                action='EMAIL_SENT',
                channel='EMAIL',
                details=f'Email sent to {notification.recipient.email}'
            )

            logger.info(f"✅ Email sent for notification #{notification.id}")
            return True

        except Exception as e:
            # Log email failure
            NotificationLog.objects.create(
                notification=notification,
                action='EMAIL_FAILED',
                channel='EMAIL',
                details=f'Email failed: {str(e)}'
            )
            logger.error(f"❌ Error sending email: {str(e)}")
            return False

    @staticmethod
    def mark_as_read(notification_id, account):
        """
        Mark notification as read
        """
        try:
            notification = Notification.objects.get(id=notification_id, recipient=account)
            notification.mark_as_read()

            # Log the action
            NotificationLog.objects.create(
                notification=notification,
                action='READ',
                channel='IN_APP',
                details=f'Marked as read by {account.account_number}'
            )

            return True

        except Notification.DoesNotExist:
            logger.error(f"❌ Notification not found or not authorized: {notification_id}")
            return False
        except Exception as e:
            logger.error(f"❌ Error marking as read: {str(e)}")
            return False

    @staticmethod
    def get_unread_notifications(account):
        """
        Get unread notifications for account
        """
        try:
            return Notification.objects.filter(
                recipient=account,
                status='UNREAD'
            ).order_by('-created_at')
        except Exception as e:
            logger.error(f"❌ Error getting notifications: {str(e)}")
            return []

    @staticmethod
    def cleanup_old_notifications(days=30):
        """
        Clean up old notifications
        """
        try:
            cutoff_date = timezone.now() - timedelta(days=days)
            old_count, _ = Notification.objects.filter(
                created_at__lt=cutoff_date,
                status='READ'
            ).delete()

            logger.info(f"✅ Cleaned up {old_count} old notifications")
            return old_count

        except Exception as e:
            logger.error(f"❌ Error cleaning up notifications: {str(e)}")
            return 0

    @staticmethod
    def get_unread_count(account_number):
        """
        Get count of unread notifications for account number

        Args:
            account_number: Account number string
        """
        try:
            return Notification.objects.filter(
                recipient__account_number=account_number,
                status='UNREAD'
            ).count()
        except Exception as e:
            logger.error(f"❌ Error getting unread count: {str(e)}")
            return 0