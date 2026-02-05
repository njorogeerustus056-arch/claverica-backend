import os
import sys
import django
import time

# Setup Django - MUST be in parent directory
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

print("=" * 60)
print("?? TESTING USER SIGNALS WITH WALLET CREATION")
print("=" * 60)

from accounts.models import Account
from users.models import UserProfile, UserSettings
from transactions.models import Wallet

# Generate unique test data
timestamp = int(time.time())
test_email = f"user_wallet_test_{timestamp}@example.com"
test_phone = f"777{timestamp}"[:20]

print(f"\n?? Creating test user:")
print(f"   Email: {test_email}")
print(f"   Phone: {test_phone}")

try:
    # Create account - should trigger users/signals.py
    print("\n1. Creating Account...")
    account = Account.objects.create(
        email=test_email,
        phone=test_phone,
        date_of_birth='1990-01-01',
        first_name='Wallet',
        last_name='Test'
    )
    print(f"   ? Account: {account.account_number}")
    
    # Check all components
    print("\n2. Checking auto-created components...")
    
    # Check UserProfile
    try:
        profile = UserProfile.objects.get(account=account)
        print(f"   ?? UserProfile: {profile.id}")
        print(f"      Name: {profile.first_name} {profile.last_name}")
    except UserProfile.DoesNotExist:
        print("   ? UserProfile NOT created!")
    
    # Check UserSettings
    try:
        settings = UserSettings.objects.get(account=account)
        print(f"   ??  UserSettings: {settings.id}")
    except UserSettings.DoesNotExist:
        print("   ? UserSettings NOT created!")
    
    # Check Wallet (CRITICAL!)
    try:
        wallet = Wallet.objects.get(account=account)
        print(f"   ?? Wallet: {wallet.id}")
        print(f"      Balance: {wallet.balance} {wallet.currency}")
        print(f"      Created: {wallet.created_at}")
    except Wallet.DoesNotExist:
        print("   ??? WALLET NOT CREATED! ???")
    
    # Test WalletService
    print("\n3. Testing WalletService...")
    if hasattr(account, 'wallet'):
        from transactions.services import WalletService
        from decimal import Decimal
        
        # Add money
        new_balance = WalletService.credit_wallet(
            account.account_number,
            Decimal('1000.00'),
            "TEST-CREDIT",
            "Test deposit"
        )
        print(f"   ?? Added 1000.00: Balance = {new_balance}")
        
        # Check transaction
        history = WalletService.get_transaction_history(account.account_number)
        if history:
            print(f"   ?? Found {len(history)} transaction(s)")
            for tx in history[:3]:  # Show first 3
                print(f"      - {tx.timestamp:%H:%M:%S}: {tx.transaction_type} {tx.amount}")
        else:
            print("   ??  No transactions found")
    else:
        print("   ??  Cannot test WalletService - no wallet")
    
    print("\n" + "=" * 60)
    print("? TEST COMPLETE")
    print(f"\nTest Account Details:")
    print(f"   Email: {account.email}")
    print(f"   Account#: {account.account_number}")
    if hasattr(account, 'wallet'):
        print(f"   Wallet: {account.wallet.id}")
        print(f"   Balance: ${account.wallet.balance}")
    
except Exception as e:
    print(f"\n? TEST FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
