#!/usr/bin/env python
import os
import sys
import django
from decimal import Decimal

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from accounts.models import Account
from transactions.models import Wallet
from transactions.services import WalletService
import time

def test_wallet_creation():
    """Test if wallets are auto-created and WalletService works"""
    
    print("=" * 60)
    print("?? COMPREHENSIVE WALLET SYSTEM TEST")
    print("=" * 60)
    
    # Create unique test account
    timestamp = int(time.time())
    test_email = f"final_test_{timestamp}@example.com"
    test_phone = f"555{timestamp:010d}"[:20]
    
    print(f"\n?? Creating test account:")
    print(f"   Email: {test_email}")
    print(f"   Phone: {test_phone}")
    
    try:
        # 1. CREATE ACCOUNT
        print("\n1. Creating Account...")
        account = Account.objects.create(
            email=test_email,
            phone=test_phone,
            date_of_birth='1990-01-01'
        )
        print(f"   ? Account: {account.account_number}")
        
        # 2. CHECK WALLET AUTO-CREATION
        print("\n2. Checking Wallet Auto-Creation...")
        try:
            wallet = Wallet.objects.get(account=account)
            print(f"   ? Wallet auto-created: {wallet.id}")
            print(f"   ? Balance: {wallet.balance} {wallet.currency}")
        except Wallet.DoesNotExist:
            print("   ? WALLET NOT AUTO-CREATED!")
            print("   Creating wallet manually...")
            wallet = Wallet.objects.create(account=account)
            print(f"   ? Manual wallet: {wallet.id}")
        
        # 3. TEST WALLETSERVICE
        print("\n3. Testing WalletService...")
        
        # Get balance
        balance = WalletService.get_balance(account.account_number)
        print(f"   ? Current balance: {balance}")
        
        # Credit $1000
        print("\n   Testing Credit ($1000)...")
        new_balance = WalletService.credit_wallet(
            account.account_number,
            Decimal('1000.00'),
            "PAY-001",
            "Initial deposit"
        )
        print(f"   ? New balance after credit: {new_balance}")
        
        # Debit $350.75
        print("\n   Testing Debit ($350.75)...")
        new_balance = WalletService.debit_wallet(
            account.account_number,
            Decimal('350.75'),
            "XFER-001",
            "Bank transfer"
        )
        print(f"   ? New balance after debit: {new_balance}")
        
        # Try to debit more than available (should fail)
        print("\n   Testing Insufficient Funds...")
        try:
            WalletService.debit_wallet(
                account.account_number,
                Decimal('1000.00'),
                "XFER-002",
                "Should fail"
            )
            print("   ? ERROR: Should have raised InsufficientFundsError!")
        except Exception as e:
            print(f"   ? Correctly failed: {str(e)[:80]}...")
        
        # Get transaction history
        print("\n   Transaction History:")
        history = WalletService.get_transaction_history(account.account_number)
        
        if history:
            for tx in history:
                print(f"\n     ?? {tx.timestamp:%Y-%m-%d %H:%M:%S}")
                print(f"       Type: {tx.transaction_type}")
                print(f"       Amount: {tx.amount}")
                print(f"       Ref: {tx.reference}")
                print(f"       Desc: {tx.description}")
                print(f"       Balance: {tx.balance_before} ? {tx.balance_after}")
        else:
            print("     No transactions found")
        
        # 4. FINAL BALANCE CHECK
        print("\n4. Final Verification...")
        final_wallet = Wallet.objects.get(account=account)
        final_balance = WalletService.get_balance(account.account_number)
        
        print(f"   Wallet balance (direct): {final_wallet.balance}")
        print(f"   Wallet balance (service): {final_balance}")
        
        if abs(final_wallet.balance - final_balance) < Decimal('0.01'):
            print("   ? Balances match!")
        else:
            print("   ? Balances don't match!")
        
        # 5. CLEANUP
        print(f"\n?? Test Account Created:")
        print(f"   Email: {account.email}")
        print(f"   Account#: {account.account_number}")
        print(f"   Wallet ID: {wallet.id}")
        print(f"   Final Balance: {final_balance}")
        
        print("\n??  To delete test account:")
        print(f'   Account.objects.filter(email="{test_email}").delete()')
        
    except Exception as e:
        print(f"\n? TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("?? TEST COMPLETE")

if __name__ == "__main__":
    test_wallet_creation()
