"""
payments/services.py - Payment processing services
"""
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from decimal import Decimal
import random
import string
from datetime import datetime

from .models import Payment, PaymentCode
from accounts.models import Account


class PaymentServiceError(Exception):
    """Custom error for payment service"""
    pass


class PaymentService:
    """
    Service for processing payments (credits) to accounts
    """

    @staticmethod
    def generate_reference():
        """Generate unique payment reference"""
        timestamp = timezone.now().strftime('%Y%m%d')
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"PAY-{timestamp}-{random_str}"

    @staticmethod
    def get_payment_code_details(payment_code):
        """
        Get account details for a payment code
        Returns: (account, payment_code_obj)
        """
        try:
            payment_code_obj = PaymentCode.objects.get(
                code=payment_code,
                is_active=True
            )
            return payment_code_obj.account, payment_code_obj
        except PaymentCode.DoesNotExist:
            raise PaymentServiceError(f"Payment code '{payment_code}' not found or inactive")

    @staticmethod
    def process_payment(payment_code, amount, sender, description=""):
        """
        Process a payment (credit) to an account

        Args:
            payment_code: Custom code (e.g., 'UASIP57EEO')
            amount: Decimal amount to credit
            sender: Sender name (e.g., 'ecovera')
            description: Optional description

        Returns:
            Payment object
        """
        # Validate amount
        try:
            amount = Decimal(str(amount))
            if amount <= Decimal('0.00'):
                raise PaymentServiceError("Amount must be positive")
        except:
            raise PaymentServiceError("Invalid amount format")

        # Get account details
        try:
            account, payment_code_obj = PaymentService.get_payment_code_details(payment_code)
        except PaymentServiceError as e:
            raise e

        # Check if account has wallet
        if not hasattr(account, 'wallet'):
            raise PaymentServiceError(f"Account {account.account_number} has no wallet")

        # Generate reference
        reference = PaymentService.generate_reference()

        try:
            # Import here to avoid circular imports
            from transactions.services import WalletService

            # Get current balance
            balance_before = account.wallet.balance

            # Credit the wallet
            balance_after = WalletService.credit_wallet(
                account_number=account.account_number,
                amount=amount,
                reference=reference,
                description=f"Payment from {sender}: {description}"
            )

            # Create payment record
            payment = Payment.objects.create(
                account=account,
                payment_code=payment_code_obj,
                amount=amount,
                sender=sender,
                reference=reference,
                description=description,
                status='completed',
                balance_before=balance_before,
                balance_after=balance_after,
                metadata={
                    'processed_by': 'admin',
                    'payment_method': 'manual_credit',
                    'sender': sender,
                    'original_payment_code': payment_code,
                }
            )

            # Send email notification
            PaymentService.send_payment_notification(payment)

            return payment

        except Exception as e:
            # Log the error
            error_ref = f"ERR-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            raise PaymentServiceError(
                f"Payment failed [{error_ref}]. Error: {str(e)}"
            )

    @staticmethod
    def send_payment_notification(payment):
        """
        Send email notification for payment

        This should be called after process_payment
        """
        try:
            # Format the date and time
            now = timezone.now()
            date_str = now.strftime("%d/%m/%y")  # 28/1/26 format
            time_str = now.strftime("%I:%M %p").lstrip('0')  # 8:01 PM format

            # Prepare email content
            subject = f"Payment Received - {payment.reference}"
            formatted_amount = f"${payment.amount:,.2f}"

            body = f"""{payment.payment_code.code if payment.payment_code else "Payment"} Confirmed.

You have received {formatted_amount} from {payment.sender}
on {date_str} at {time_str}.

New ACCOUNT balance is ${payment.balance_after:,.2f}

Reference: {payment.reference}
Account: {payment.account.account_number}

Thank you for using our service.
"""

            # Get recipient email
            recipient_email = payment.account.email
            
            # Send email using Django's email backend
            try:
                send_mail(
                    subject=subject,
                    message=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,  # Configure this in settings.py
                    recipient_list=[recipient_email],
                    fail_silently=False,  # Set to True in production to avoid crashing if email fails
                )
                
                print(f"\n[EMAIL SENT] Payment notification to {recipient_email}")
                print(f"Subject: {subject}")
                print(f"Amount: {formatted_amount}")
                
                return True
                
            except Exception as email_error:
                # Fallback to logging if email fails
                print(f"\n[EMAIL FAILED] Could not send to {recipient_email}")
                print(f"Error: {email_error}")
                
                # Log the email that would have been sent
                print("\n" + "="*60)
                print(" PAYMENT EMAIL NOTIFICATION (FALLBACK)")
                print("="*60)
                print(f"To: {recipient_email}")
                print(f"Subject: {subject}")
                print(f"\nBody:\n{body}")
                print("="*60)
                
                # Return False but don't fail the entire payment
                # In production, you might want to use a task queue
                return False

        except Exception as e:
            print(f"[ERROR] Failed to prepare notification: {e}")
            return False

    @staticmethod
    def get_payment_history(account_number, limit=50):
        """Get payment history for an account"""
        try:
            account = Account.objects.get(account_number=account_number)
            return Payment.objects.filter(account=account).order_by('-created_at')[:limit]
        except Account.DoesNotExist:
            return []

    @staticmethod
    def assign_payment_code(account, code):
        """Assign a payment code to an account"""
        if PaymentCode.objects.filter(code=code).exists():
            raise PaymentServiceError(f"Payment code '{code}' already in use")

        if hasattr(account, 'payment_code'):
            raise PaymentServiceError(f"Account already has payment code: {account.payment_code.code}")

        payment_code = PaymentCode.objects.create(
            account=account,
            code=code
        )

        return payment_code

    @staticmethod
    def deactivate_payment_code(payment_code):
        """Deactivate a payment code"""
        try:
            pc = PaymentCode.objects.get(code=payment_code)
            pc.is_active = False
            pc.save()
            return pc
        except PaymentCode.DoesNotExist:
            raise PaymentServiceError(f"Payment code '{payment_code}' not found")