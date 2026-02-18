"""
cards/services.py - Get cardholder name from User model
"""
from django.conf import settings
from .models import Card, CardStatus
from .exceptions import CardException, CardNotFoundException
from transactions.services import WalletService
from decimal import Decimal
import random
import time
import logging

logger = logging.getLogger(__name__)


class CardService:
    """Card service for business logic"""

    @staticmethod
    def generate_card_number(account_id):
        """Generate unique card number"""
        timestamp = int(time.time() * 1000)
        random_part = random.randint(1000, 9999)
        base_number = f"{timestamp}{random_part}{account_id}"

        # Ensure 16 digits
        while len(base_number) < 16:
            base_number += str(random.randint(0, 9))

        card_number = base_number[:16]
        card_number = CardService._add_luhn_check_digit(card_number)
        return card_number

    @staticmethod
    def _add_luhn_check_digit(number):
        """Add Luhn check digit"""
        total = 0
        reverse_digits = number[::-1]

        for i, digit in enumerate(reverse_digits):
            n = int(digit)
            if i % 2 == 0:
                n *= 2
                if n > 9:
                    n -= 9
            total += n

        check_digit = (10 - (total % 10)) % 10
        return number + str(check_digit)

    @staticmethod
    def create_card(account, card_type='virtual', is_primary=False, **kwargs):
        """Create a new card for account"""
        try:
            # If setting as primary, unset existing primary
            if is_primary:
                Card.objects.filter(account=account, is_primary=True).update(is_primary=False)

            # Generate card details
            card_number = CardService.generate_card_number(account.id)
            last_four = card_number[-4:]

            # Generate CVV
            cvv = str(random.randint(100, 999))

            # Set expiry date
            from django.utils import timezone
            now = timezone.now()
            expiry_month = now.month
            expiry_year = (now.year + 3) % 100
            expiry_date = f"{expiry_month:02d}/{expiry_year:02d}"

            # Get user's name from Account (which IS User)
            cardholder_name = kwargs.get('cardholder_name', '')
            if not cardholder_name:
                # FIXED: Account extends AbstractUser, so it has first_name, last_name, email
                name = f"{account.first_name} {account.last_name}".strip()
                cardholder_name = name if name else account.email

            # Create card
            card = Card.objects.create(
                account=account,
                card_type=card_type,
                card_number=card_number,
                last_four=last_four,
                expiry_date=expiry_date,
                cardholder_name=cardholder_name,
                status=CardStatus.ACTIVE,
                color_scheme=kwargs.get('color_scheme', 'blue-gradient'),
                is_primary=is_primary
            )

            # Log card creation without exposing CVV
            logger.info(f"Card created successfully for account {account.email} with last four {last_four}")
            
            # In development, you might want to show CVV in console for testing
            if settings.DEBUG:
                print(f"[DEV ONLY] CVV for card ****{last_four}: {cvv}")
                print("[DEV ONLY] This should be shown to user only once and not stored!")

            return card

        except Exception as e:
            raise CardException(f"Failed to create card: {str(e)}")

    @staticmethod
    def get_account_cards(account):
        """Get all cards for account"""
        return Card.objects.filter(account=account).order_by('-is_primary', '-created_at')

    @staticmethod
    def get_primary_card(account):
        """Get account's primary card"""
        try:
            return Card.objects.get(account=account, is_primary=True)
        except Card.DoesNotExist:
            return None
