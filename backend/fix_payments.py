import os
import django
import sys

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from accounts.models import Account
from payments.models import Payment
from transactions.models import Wallet, Transaction

def fix_account_payments(account_id):
    """Fix wallet and transactions for a specific account"""
    try:
        account = Account.objects.get(id=account_id)
        print(f"Fixing account: {account.account_number}")
        
        # Get or create wallet
        wallet, created = Wallet.objects.get_or_create(
            account=account,
            defaults={'balance': 0.00, 'currency': 'USD'}
        )
        
        print(f"Wallet: {wallet.id}, Created: {created}, Current balance: ${wallet.balance}")
        
        # Get all completed payments
        payments = Payment.objects.filter(account=account, status='completed')
        total_amount = sum(p.amount for p in payments)
        
        print(f"\nFound {payments.count()} completed payments totaling: ${total_amount}")
        
        if payments.count() > 0:
            # Update wallet
            wallet.balance = total_amount
            wallet.save()
            
            print(f"Updated wallet balance to: ${wallet.balance}")
            
            # Create transactions for each payment
            for payment in payments:
                # Update payment balances if needed
                if payment.balance_before == 0.00:
                    payment.balance_before = wallet.balance - payment.amount
                    payment.balance_after = wallet.balance
                    payment.save(update_fields=['balance_before', 'balance_after'])
                
                # Calculate wallet balance for this transaction
                balance_before = max(0, wallet.balance - payment.amount)
                balance_after = wallet.balance
                
                # Check if transaction already exists
                try:
                    transaction = Transaction.objects.get(reference=payment.reference)
                    print(f"  - Payment {payment.reference}: ${payment.amount} | Transaction already exists: {transaction.id}")
                except Transaction.DoesNotExist:
                    # Create transaction
                    transaction = Transaction.objects.create(
                        wallet=wallet,
                        transaction_type='payment_in',
                        amount=payment.amount,
                        reference=payment.reference,
                        description=f'Payment from {payment.sender}',
                        balance_before=balance_before,
                        balance_after=balance_after,
                        metadata={
                            'payment_id': str(payment.id),
                            'payment_reference': payment.reference,
                            'sender': payment.sender
                        }
                    )
                    print(f"  - Payment {payment.reference}: ${payment.amount} | Created transaction: {transaction.id}")
            
            print(f"\n✅ Done! Wallet balance: ${wallet.balance}")
        else:
            print("No completed payments found for this account.")
            
    except Account.DoesNotExist:
        print(f"Account with ID {account_id} does not exist.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Fix account ID 17
    fix_account_payments(17)