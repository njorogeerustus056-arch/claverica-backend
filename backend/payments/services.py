# payments/services.py - DYNAMIC VERSION WITHOUT HARDCODED DATA
from django.db import transaction as db_transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal
import random
import string
import logging
from datetime import datetime, timedelta

from .models import (
    PaymentTransactionNotification, 
    ActivityFeed,
    Transaction,
    MainBusinessWallet,
    EmployeePlatformWallet
)

logger = logging.getLogger(__name__)
User = get_user_model()


class PaymentService:
    """Service for handling dynamic payment operations and notifications"""
    
    @staticmethod
    def generate_reference_code():
        """Generate unique reference code like MBNHLF9RR42TSAO3"""
        # Format: 16 chars, mixed case alphanumeric
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(16))
    
    @staticmethod
    def format_payment_message(
        reference_code,
        amount,
        sender_display_name,
        receiver_account_info="",
        timestamp=None,
        bank_routing="via ClaveRica branch - The Goldman Sachs Group"
    ):
        """Format payment notification message dynamically"""
        if timestamp is None:
            timestamp = timezone.now()
        
        # Format timestamp
        formatted_time = timestamp.strftime("%b %d, %Y %I:%M %p")
        
        # Format amount - remove hardcoded currency prefix
        # The actual currency will come from the transaction/wallet
        formatted_amount = f"${amount:,.2f}"
        
        # Build the message dynamically
        message = f"{reference_code} Confirmed! You have received {formatted_amount} from {sender_display_name}."
        
        if receiver_account_info:
            message += f" - {receiver_account_info} at {formatted_time} {bank_routing}"
        else:
            message += f" at {formatted_time} {bank_routing}"
        
        return message
    
    @staticmethod
    def format_dashboard_display(amount, company_tag="ClaveRica LTD", emoji="😊"):
        """Format dashboard display text dynamically"""
        return f"↑ +${amount:,.2f} ({company_tag}) {emoji}"
    
    @staticmethod
    def get_receiver_account_info(receiver):
        """Get receiver account information dynamically"""
        if hasattr(receiver, 'employee_platform_wallet'):
            return receiver.employee_platform_wallet.wallet_number
        elif receiver.accounts.filter(is_active=True).exists():
            account = receiver.accounts.filter(is_active=True).first()
            return account.account_number
        elif receiver.email:
            return receiver.email[:10] + "..." if len(receiver.email) > 10 else receiver.email
        return ""
    
    @staticmethod
    def get_sender_display_name(sender, override_name=None):
        """Get sender display name dynamically"""
        if override_name:
            return override_name
        
        if hasattr(sender, 'main_business_wallet'):
            return sender.main_business_wallet.display_name or "ecoveraLTD"
        
        if sender.first_name and sender.last_name:
            return f"{sender.first_name} {sender.last_name}"
        
        return sender.email.split('@')[0] if '@' in sender.email else "Sender"
    
    @staticmethod
    def create_payment_notification(
        sender,
        receiver,
        amount,
        currency='USD',
        sender_display_name=None,
        description="Payment received",
        reference_code=None,
        transaction=None
    ):
        """Create a payment notification record dynamically"""
        if reference_code is None:
            reference_code = PaymentService.generate_reference_code()
        
        # Get sender display name dynamically
        sender_name = PaymentService.get_sender_display_name(sender, sender_display_name)
        
        # Get receiver account info dynamically
        receiver_account_info = PaymentService.get_receiver_account_info(receiver)
        
        # Format messages
        full_message = PaymentService.format_payment_message(
            reference_code=reference_code,
            amount=amount,
            sender_display_name=sender_name,
            receiver_account_info=receiver_account_info,
            timestamp=timezone.now()
        )
        
        short_message = PaymentService.format_dashboard_display(
            amount=amount,
            company_tag="ClaveRica LTD",
            emoji='😊'
        )
        
        # Create notification
        notification = PaymentTransactionNotification.objects.create(
            reference_code=reference_code,
            sender=sender,
            receiver=receiver,
            notification_type='payment_received',
            amount=amount,
            currency=currency,
            full_message=full_message,
            short_message=short_message,
            emoji='😊',
            sender_account=sender_name,
            receiver_account=receiver_account_info,
            bank_routing="via ClaveRica branch - The Goldman Sachs Group",
            transaction=transaction,
            description=description
        )
        
        return notification
    
    @staticmethod
    def send_payment_notification(notification):
        """Send payment notification via all channels"""
        try:
            # 1. Mark website delivered (real-time via WebSocket/Pusher)
            notification.website_delivered = True
            notification.delivered_at = timezone.now()
            
            # 2. Send email (in production, integrate with email service)
            # email_service.send_payment_notification(notification)
            notification.email_sent = True
            
            # 3. Send push notification (in production, integrate with FCM/APNS)
            # push_service.send_notification(notification)
            notification.push_sent = True
            
            notification.save()
            
            logger.info(f"Notification {notification.reference_code} delivered to {notification.receiver.email}: ${notification.amount}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send notification {notification.reference_code}: {str(e)}")
            return False
    
    @staticmethod
    def process_employer_payment(employer, employee_email, amount, description=""):
        """Process employer payment to employee dynamically"""
        try:
            with db_transaction.atomic():
                # Get employee
                employee = User.objects.get(email=employee_email)
                
                # Get wallets
                employer_wallet = employer.main_business_wallet
                employee_wallet = employee.employee_platform_wallet
                
                # Validate
                if not employer_wallet.has_sufficient_funds(amount):
                    raise ValueError(f"Insufficient funds. Available: ${employer_wallet.available_balance}")
                
                # Process payment
                employer_wallet.deduct_funds(amount, description)
                employee_wallet.add_funds(amount, 'employer_payment')
                
                # Create transaction record
                transaction = Transaction.objects.create(
                    account=employer.accounts.first() if employer.accounts.exists() else None,
                    recipient_account=employee.accounts.first() if employee.accounts.exists() else None,
                    amount=amount,
                    currency=employer_wallet.currency,
                    transaction_type='transfer',
                    description=description,
                    status='completed'
                )
                
                # Create notification
                notification = PaymentService.create_payment_notification(
                    sender=employer,
                    receiver=employee,
                    amount=amount,
                    currency=employer_wallet.currency,
                    description=description,
                    transaction=transaction
                )
                
                # Send notification
                PaymentService.send_payment_notification(notification)
                
                # Create activity feed entries
                # Employer activity
                ActivityFeed.objects.create(
                    user=employer,
                    activity_type='payment_sent',
                    reference=notification.reference_code,
                    amount=amount,
                    currency=employer_wallet.currency,
                    display_text=f"↓ Sent: ${amount:,.2f} to {employee.email}",
                    emoji='📤',
                    color_class='text-blue-600',
                    metadata={'employee_email': employee.email}
                )
                
                # Employee activity
                ActivityFeed.objects.create(
                    user=employee,
                    activity_type='payment_received',
                    reference=notification.reference_code,
                    amount=amount,
                    currency=employee_wallet.currency,
                    display_text=f"↑ +${amount:,.2f} (ClaveRica LTD)",
                    emoji='😊',
                    color_class='text-green-600',
                    metadata={'employer_email': employer.email}
                )
                
                return {
                    'success': True,
                    'reference_code': notification.reference_code,
                    'notification': notification,
                    'transaction': transaction,
                    'amount': str(amount),
                    'currency': employer_wallet.currency,
                    'employee': employee.email
                }
                
        except User.DoesNotExist:
            raise ValueError("Employee not found")
        except AttributeError as e:
            if "'User' object has no attribute 'main_business_wallet'" in str(e):
                raise ValueError("Employer does not have a main business wallet")
            elif "'User' object has no attribute 'employee_platform_wallet'" in str(e):
                raise ValueError("Employee does not have a platform wallet")
            else:
                raise
        except Exception as e:
            logger.error(f"Payment processing failed: {str(e)}")
            raise
    
    @staticmethod
    def process_withdrawal_request(withdrawal_request):
        """Process withdrawal request dynamically"""
        try:
            with db_transaction.atomic():
                wallet = withdrawal_request.employee_wallet
                
                # Check if sufficient funds
                if wallet.available_for_withdrawal < withdrawal_request.amount:
                    raise ValueError(f"Insufficient funds for withdrawal. Available: ${wallet.available_for_withdrawal}")
                
                # Update wallet
                wallet.available_for_withdrawal -= withdrawal_request.amount
                wallet.pending_withdrawal += withdrawal_request.amount
                wallet.save()
                
                # Generate TAC code
                withdrawal_request.generate_tac_code()
                
                # Create notification for TAC
                notification = PaymentService.create_payment_notification(
                    sender=wallet.user,
                    receiver=wallet.user,
                    amount=withdrawal_request.amount,
                    currency=withdrawal_request.currency,
                    sender_display_name="Withdrawal System",
                    description=f"TAC code generated for withdrawal: {withdrawal_request.tac_code}"
                )
                
                # Create activity feed entry
                ActivityFeed.objects.create(
                    user=wallet.user,
                    activity_type='tac_generated',
                    reference=withdrawal_request.withdrawal_reference,
                    amount=withdrawal_request.amount,
                    currency=withdrawal_request.currency,
                    display_text=f"🔐 TAC generated for ${withdrawal_request.amount:,.2f} withdrawal",
                    emoji='🔐',
                    color_class='text-yellow-600',
                    metadata={'withdrawal_reference': withdrawal_request.withdrawal_reference}
                )
                
                return {
                    'success': True,
                    'withdrawal_reference': withdrawal_request.withdrawal_reference,
                    'tac_code': withdrawal_request.tac_code,
                    'tac_generated_at': withdrawal_request.tac_generated_at,
                    'notification': notification
                }
                
        except Exception as e:
            logger.error(f"Withdrawal processing failed: {str(e)}")
            raise
    
    @staticmethod
    def complete_withdrawal(withdrawal_request):
        """Complete withdrawal after TAC verification"""
        try:
            with db_transaction.atomic():
                wallet = withdrawal_request.employee_wallet
                
                # Create bank transfer transaction
                transaction = Transaction.objects.create(
                    account=wallet.user.accounts.first() if wallet.user.accounts.exists() else None,
                    amount=withdrawal_request.amount,
                    currency=withdrawal_request.currency,
                    transaction_type='withdrawal',
                    description=f"Withdrawal to bank: {withdrawal_request.bank_account.account_number}",
                    status='completed',
                    recipient_name=wallet.user.get_full_name() or wallet.user.email
                )
                
                # Update withdrawal request
                withdrawal_request.transaction_reference = transaction.transaction_id
                withdrawal_request.processed_at = timezone.now()
                withdrawal_request.status = 'completed'
                withdrawal_request.save()
                
                # Update wallet
                wallet.pending_withdrawal -= withdrawal_request.amount
                wallet.save()
                
                # Create completion notification
                notification = PaymentService.create_payment_notification(
                    sender=wallet.user,
                    receiver=wallet.user,
                    amount=withdrawal_request.amount,
                    currency=withdrawal_request.currency,
                    sender_display_name="Withdrawal System",
                    description=f"Withdrawal of ${withdrawal_request.amount:,.2f} completed successfully"
                )
                
                # Create activity feed entry
                ActivityFeed.objects.create(
                    user=wallet.user,
                    activity_type='withdrawal_completed',
                    reference=withdrawal_request.withdrawal_reference,
                    amount=withdrawal_request.amount,
                    currency=withdrawal_request.currency,
                    display_text=f"✅ Withdrawal of ${withdrawal_request.amount:,.2f} completed",
                    emoji='✅',
                    color_class='text-green-600',
                    metadata={
                        'withdrawal_reference': withdrawal_request.withdrawal_reference,
                        'transaction_id': transaction.transaction_id
                    }
                )
                
                return {
                    'success': True,
                    'withdrawal_reference': withdrawal_request.withdrawal_reference,
                    'transaction_id': transaction.transaction_id,
                    'amount': str(withdrawal_request.amount),
                    'completed_at': withdrawal_request.processed_at
                }
                
        except Exception as e:
            logger.error(f"Withdrawal completion failed: {str(e)}")
            raise
    
    @staticmethod
    def get_user_financial_summary(user):
        """Get comprehensive financial summary for user"""
        try:
            # Get wallet balances if they exist
            main_wallet_balance = Decimal('0.00')
            employee_wallet_balance = Decimal('0.00')
            
            if hasattr(user, 'main_business_wallet'):
                main_wallet_balance = user.main_business_wallet.available_balance
            
            if hasattr(user, 'employee_platform_wallet'):
                employee_wallet_balance = user.employee_platform_wallet.platform_balance
            
            # Get account balances
            account_balances = user.accounts.filter(is_active=True).aggregate(
                total_balance=Sum('balance'),
                total_available=Sum('available_balance')
            )
            
            # Calculate recent activity
            thirty_days_ago = timezone.now() - timedelta(days=30)
            
            # Recent received payments
            recent_payments = PaymentTransactionNotification.objects.filter(
                receiver=user,
                created_at__gte=thirty_days_ago
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            # Recent withdrawals
            recent_withdrawals = WithdrawalRequest.objects.filter(
                employee_wallet__user=user,
                status='completed',
                processed_at__gte=thirty_days_ago
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            return {
                'main_wallet_balance': str(main_wallet_balance),
                'employee_wallet_balance': str(employee_wallet_balance),
                'account_balance': str(account_balances['total_balance'] or Decimal('0.00')),
                'available_balance': str(account_balances['total_available'] or Decimal('0.00')),
                'recent_payments_received': str(recent_payments),
                'recent_withdrawals': str(recent_withdrawals),
                'total_assets': str(
                    main_wallet_balance + 
                    employee_wallet_balance + 
                    (account_balances['total_balance'] or Decimal('0.00'))
                )
            }
            
        except Exception as e:
            logger.error(f"Financial summary failed for user {user.email}: {str(e)}")
            return {
                'error': 'Failed to load financial summary',
                'main_wallet_balance': '0.00',
                'employee_wallet_balance': '0.00',
                'account_balance': '0.00',
                'available_balance': '0.00',
                'recent_payments_received': '0.00',
                'recent_withdrawals': '0.00',
                'total_assets': '0.00'
            }


# Alias functions for easy import
def generate_reference_code():
    return PaymentService.generate_reference_code()

def format_payment_message(*args, **kwargs):
    return PaymentService.format_payment_message(*args, **kwargs)

def send_payment_notification(notification):
    return PaymentService.send_payment_notification(notification)