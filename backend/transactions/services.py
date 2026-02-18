"""
transactions/services.py - Wallet service for balance operations
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from decimal import Decimal
import time
from .models import Wallet, Transaction


class WalletServiceError(Exception):
    """Custom error for wallet service"""
    pass


class InsufficientFundsError(WalletServiceError):
    """Raised when trying to debit more than available balance"""
    pass


class WalletService:
    """Service for wallet operations"""

    @staticmethod
    def get_wallet(account_number):
        """Get wallet for account"""
        try:
            from accounts.models import Account
            account = Account.objects.get(account_number=account_number)
            return account.wallet
        except Account.DoesNotExist:
            raise WalletServiceError(f"Account {account_number} not found")
        except AttributeError:
            raise WalletServiceError(f"Account {account_number} has no wallet")

    @staticmethod
    def get_balance(account_number):
        """Get current wallet balance"""
        wallet = WalletService.get_wallet(account_number)
        return wallet.balance

    @staticmethod
    def credit_wallet(account_number, amount, reference="", description=""):
        """
        Credit (add money to) wallet

        Args:
            account_number: CLV account number
            amount: Decimal amount to add
            reference: Payment reference
            description: Transaction description

        Returns:
            New balance after credit
        """
        try:
            amount = Decimal(str(amount))
            if amount <= Decimal('0.00'):
                raise WalletServiceError("Amount must be positive")
        except:
            raise WalletServiceError("Invalid amount format")

        wallet = WalletService.get_wallet(account_number)

        # Check if Transaction model exists
        try:
            # Create transaction record if Transaction model exists
            Transaction.objects.create(
                wallet=wallet,
                transaction_type='credit',
                amount=amount,
                reference=reference,
                description=description,
                balance_before=wallet.balance,
                balance_after=wallet.balance + amount,
                metadata={'source': 'payment', 'reference': reference}
            )
        except:
            # If Transaction model doesn't exist yet, just log
            print(f"Credit: {amount} to {account_number}. Reference: {reference}")

        # Update balance
        wallet.balance += amount
        wallet.save()

        return wallet.balance

    @staticmethod
    def debit_wallet(account_number, amount, reference="", description=""):
        """
        Debit (remove money from) wallet

        Args:
            account_number: CLV account number
            amount: Decimal amount to remove
            reference: Payment reference
            description: Transaction description

        Returns:
            New balance after debit
        """
        try:
            amount = Decimal(str(amount))
            if amount <= Decimal('0.00'):
                raise WalletServiceError("Amount must be positive")
        except:
            raise WalletServiceError("Invalid amount format")

        wallet = WalletService.get_wallet(account_number)

        # Check sufficient funds
        if wallet.balance < amount:
            raise InsufficientFundsError(
                f"Insufficient funds. Available: {wallet.balance}, Requested: {amount}"
            )

        # Check if Transaction model exists
        try:
            # Create transaction record if Transaction model exists
            Transaction.objects.create(
                wallet=wallet,
                transaction_type='debit',
                amount=amount,
                reference=reference,
                description=description,
                balance_before=wallet.balance,
                balance_after=wallet.balance - amount,
                metadata={'source': 'transfer', 'reference': reference}
            )
        except:
            # If Transaction model doesn't exist yet, just log
            print(f"Debit: {amount} from {account_number}. Reference: {reference}")

        # Update balance
        wallet.balance -= amount
        wallet.save()

        return wallet.balance

    @staticmethod
    def transfer(source_account, target_account, amount, reference="", description=""):
        """
        Transfer between two wallets

        Args:
            source_account: Sender account number
            target_account: Receiver account number
            amount: Transfer amount
            reference: Transfer reference
            description: Transfer description

        Returns:
            Tuple (new_source_balance, new_target_balance)
        """
        # Debit from source
        new_source_balance = WalletService.debit_wallet(
            source_account, amount, reference, f"Transfer to {target_account}: {description}"
        )

        # Credit to target
        new_target_balance = WalletService.credit_wallet(
            target_account, amount, reference, f"Transfer from {source_account}: {description}"
        )

        return new_source_balance, new_target_balance
