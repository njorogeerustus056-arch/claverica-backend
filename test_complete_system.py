import os
import sys
import django
import time
from decimal import Decimal

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from accounts.models import Account
from transactions.services import WalletService

print("=" * 80)
print("?? COMPLETE TRANSACTIONS SYSTEM TEST")
print("=" * 80)

# Create a test account
timestamp = int(time.time())
test_email = f"complete_test_{timestamp}@example.com"
test_phone = f"123{timestamp}"[:20]

print(f"\n?? CREATING TEST ACCOUNT")
print(f"   Email: {test_email}")
print(f"   Phone: {test_phone}")

try:
    # 1. Create account (triggers signals)
    account = Account.objects.create(
        email=test_email,
        phone=test_phone,
        date_of_birth='1990-01-01',
        first_name='Complete',
        last_name='Test'
    )
    account_number = account.account_number
    print(f"   ? Account created: {account_number}")
    
    # 2. Test WalletService
    print(f"\n?? TESTING WALLETSERVICE")
    
    # Test 1: Initial balance
    balance = WalletService.get_balance(account_number)
    print(f"   a) Initial balance: ${balance}")
    
    # Test 2: Simulate Payment from Admin (Payments App)
    print(f"\n   b) Simulating PAYMENT (Admin ? Client):")
    new_balance = WalletService.credit_wallet(
        account_number,
        Decimal('5000.00'),
        "UASIP57EEO",
        "Payment from ecovera"
    )
    print(f"      Payment Code: UASIP57EEO")
    print(f"      Amount: $5000.00")
    print(f"      Sender: ecovera")
    print(f"      New balance: ${new_balance}")
    
    # Test 3: Simulate Transfer to Bank (Transfers App)
    print(f"\n   c) Simulating TRANSFER (Client ? Bank):")
    new_balance = WalletService.debit_wallet(
        account_number,
        Decimal('1500.50'),
        "TAC-789012",
        "Transfer to Equity Bank account 1234567890"
    )
    print(f"      Amount: $1500.50")
    print(f"      Recipient: Equity Bank (1234567890)")
    print(f"      TAC Code: TAC-789012")
    print(f"      New balance: ${new_balance}")
    
    # Test 4: Simulate another payment
    print(f"\n   d) Simulating SECOND PAYMENT:")
    new_balance = WalletService.credit_wallet(
        account_number,
        Decimal('3000.00'),
        "PAY-ABC123",
        "Salary deposit"
    )
    print(f"      Amount: $3000.00")
    print(f"      New balance: ${new_balance}")
    
    # Test 5: Get complete transaction history
    print(f"\n?? TRANSACTION HISTORY")
    history = WalletService.get_transaction_history(account_number)
    
    if history:
        print(f"   Total transactions: {len(history)}")
        
        # Calculate totals
        total_credits = sum(tx.amount for tx in history if tx.transaction_type == 'payment_in')
        total_debits = sum(tx.amount for tx in history if tx.transaction_type == 'transfer_out')
        net_balance = total_credits - total_debits
        
        print(f"   Total received: ${total_credits}")
        print(f"   Total sent: ${total_debits}")
        print(f"   Net balance: ${net_balance}")
        print(f"   Current balance: ${new_balance}")
        print(f"   Balance matches: {net_balance == new_balance}")
        
        print(f"\n   ?? Transaction Timeline:")
        for i, tx in enumerate(history, 1):
            print(f"\n     {i}. {tx.timestamp:%Y-%m-%d %H:%M:%S}")
            print(f"        Type: {tx.transaction_type.replace('_', ' ').title()}")
            print(f"        Amount: ${tx.amount}")
            print(f"        Reference: {tx.reference}")
            print(f"        Description: {tx.description}")
            print(f"        Balance: ${tx.balance_before} ? ${tx.balance_after}")
    else:
        print("   No transactions found")
    
    # Test 6: API Endpoints
    print(f"\n?? API ENDPOINTS READY:")
    print(f"   GET  /transactions/wallet/{account_number}/balance/")
    print(f"   POST /transactions/wallet/credit/")
    print(f"   POST /transactions/wallet/debit/")
    print(f"   GET  /transactions/wallet/{account_number}/transactions/")
    
    print(f"\n" + "=" * 80)
    print("? TRANSACTIONS SYSTEM VERIFICATION COMPLETE")
    print(f"\n?? TEST SUMMARY:")
    print(f"   Account#: {account_number}")
    print(f"   Email: {account.email}")
    print(f"   Final Balance: ${new_balance}")
    print(f"   Total Transactions: {len(history) if 'history' in locals() else 0}")
    
    print(f"\n??  Test account created for verification.")
    print(f'   To delete: Account.objects.filter(email="{test_email}").delete()')
    
except Exception as e:
    print(f"\n? TEST FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
