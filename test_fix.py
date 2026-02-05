#!/usr/bin/env python
import os
import sys
import django
import time

# Setup Django - run from parent directory
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from accounts.models import Account
from transactions.models import Wallet
from transactions.services import WalletService
from decimal import Decimal

print("=" * 60)
print("?? TESTING SIGNAL FIX & WALLET CREATION")
print("=" * 60)

# Generate unique identifiers
timestamp = int(time.time())
test_email = f"signal_fix_{timestamp}@example.com"
test_phone = f"888{timestamp}"[:20]

print(f"\n?? Creating test account:")
print(f"   Email: {test_email}")
print(f"   Phone: {test_phone}")

try:
    # Create account - should trigger signals
    print("\n1. Creating Account (signals should trigger)...")
    account = Account.objects.create(
        email=test_email,
        phone=test_phone,
        date_of_birth='1990-01-01'
    )
    print(f"   ? Account: {account.account_number}")
    
    # Check if wallet was auto-created
    print("\n2. Checking Wallet Auto-Creation...")
    try:
        wallet = Wallet.objects.get(account=account)
        print(f"   ? Wallet auto-created: {wallet.id}")
        print(f"   ?? Balance: {wallet.balance} {wallet.currency}")
    except Wallet.DoesNotExist:
        print("   ? WALLET NOT AUTO-CREATED!")
        print("   Creating manually...")
        wallet = Wallet.objects.create(account=account)
        print(f"   ? Manual wallet: {wallet.id}")
    
    # Test WalletService
    print("\n3. Testing WalletService...")
    try:
        # Credit
        new_balance = WalletService.credit_wallet(
            account.account_number,
            Decimal('1000.00'),
            "TEST-SIGNAL",
            "Test after signal fix"
        )
        print(f"   ? Credited 1000: New balance = {new_balance}")
        
        # Verify transaction exists
        history = WalletService.get_transaction_history(account.account_number)
        print(f"   ?? Transactions: {len(history)} records")
        
        print("\n?? Test Results:")
        print(f"   Account#: {account.account_number}")
        print(f"   Wallet ID: {wallet.id}")
        print(f"   Final Balance: {new_balance}")
        
    except Exception as e:
        print(f"   ? WalletService error: {e}")
        
except Exception as e:
    print(f"\n? TEST FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("?? TEST COMPLETE")
