#!/usr/bin/env python
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
from users.models import UserProfile, UserSettings
from transactions.models import Wallet
from transactions.services import WalletService

print("=" * 70)
print("?? TESTING USER-CENTRIC SIGNAL ARCHITECTURE")
print("=" * 70)

# Generate unique test data
timestamp = int(time.time())
test_email = f"user_centric_{timestamp}@example.com"
test_phone = f"444{timestamp}"[:20]

print(f"\n?? Creating test user:")
print(f"   Email: {test_email}")
print(f"   Phone: {test_phone}")

try:
    # 1. CREATE ACCOUNT (triggers users/signals.py)
    print("\n1. Creating Account (triggers users signals)...")
    account = Account.objects.create(
        email=test_email,
        phone=test_phone,
        date_of_birth='1990-01-01',
        first_name='Signal',
        last_name='Test'
    )
    print(f"   ? Account: {account.account_number}")
    
    # 2. VERIFY ALL COMPONENTS WERE CREATED
    print("\n2. Verifying auto-created components...")
    
    # Check UserProfile
    try:
        profile = UserProfile.objects.get(account=account)
        print(f"   ?? UserProfile: {profile.id}")
        print(f"      Name: {profile.first_name} {profile.last_name}")
        print(f"      Email: {profile.email}")
    except UserProfile.DoesNotExist:
        print("   ? UserProfile NOT created!")
    
    # Check UserSettings
    try:
        settings = UserSettings.objects.get(account=account)
        print(f"   ??  UserSettings: {settings.id}")
        print(f"      Theme: {settings.theme}")
        print(f"      Language: {settings.language}")
    except UserSettings.DoesNotExist:
        print("   ? UserSettings NOT created!")
    
    # Check Wallet
    try:
        wallet = Wallet.objects.get(account=account)
        print(f"   ?? Wallet: {wallet.id}")
        print(f"      Balance: {wallet.balance} {wallet.currency}")
    except Wallet.DoesNotExist:
        print("   ? Wallet NOT created!")
    
    # 3. TEST WALLET SERVICE
    print("\n3. Testing Financial Operations...")
    if hasattr(account, 'wallet'):
        # Add money
        new_balance = WalletService.credit_wallet(
            account.account_number,
            Decimal('1500.00'),
            "SALARY-001",
            "Monthly salary"
        )
        print(f"   ?? Credited 1500.00: Balance = {new_balance}")
        
        # Spend money
        new_balance = WalletService.debit_wallet(
            account.account_number,
            Decimal('299.99'),
            "SHOPPING-001",
            "Online shopping"
        )
        print(f"   ???  Debited 299.99: Balance = {new_balance}")
        
        # Get transaction history
        history = WalletService.get_transaction_history(account.account_number)
        print(f"   ?? Transaction History: {len(history)} records")
    else:
        print("   ??  Cannot test WalletService - no wallet found")
    
    # 4. FINAL SUMMARY
    print("\n" + "=" * 70)
    print("?? TEST RESULTS SUMMARY:")
    print(f"   Account#: {account.account_number}")
    print(f"   Email: {account.email}")
    
    if hasattr(account, 'userprofile'):
        print(f"   UserProfile: ? {account.userprofile.id}")
    else:
        print(f"   UserProfile: ? Missing")
        
    if hasattr(account, 'usersettings'):
        print(f"   UserSettings: ? {account.usersettings.id}")
    else:
        print(f"   UserSettings: ? Missing")
        
    if hasattr(account, 'wallet'):
        print(f"   Wallet: ? {account.wallet.id}")
        print(f"   Balance: ${account.wallet.balance}")
    else:
        print(f"   Wallet: ? Missing")
    
    print("\n??  Test account created. To delete:")
    print(f'   Account.objects.filter(email="{test_email}").delete()')
    
except Exception as e:
    print(f"\n? TEST FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("?? TEST COMPLETE")
