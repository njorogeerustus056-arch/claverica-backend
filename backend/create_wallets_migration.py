import sys
import os

# Add parent directory to path
sys.path.append('..')

import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from accounts.models import Account
from transactions.models import Wallet

print("=" * 70)
print("?? CREATING WALLETS FOR ALL EXISTING ACCOUNTS")
print("=" * 70)

# Get all accounts without wallets
accounts_without_wallets = Account.objects.filter(wallet__isnull=True)
print(f"Found {accounts_without_wallets.count()} accounts without wallets")

if accounts_without_wallets.count() > 0:
    print("\n?? Creating wallets...")
    created_count = 0
    
    for account in accounts_without_wallets:
        try:
            # Create wallet with 0.00 balance
            wallet = Wallet.objects.create(
                account=account,
                balance=0.00,
                currency='USD'
            )
            created_count += 1
            print(f"  ? Created wallet for {account.email}: {wallet.id}")
        except Exception as e:
            print(f"  ? Failed for {account.email}: {e}")
    
    print(f"\n?? Created {created_count} new wallets!")
else:
    print("\n?? All accounts already have wallets!")

# Final verification
total_accounts = Account.objects.count()
accounts_with_wallets = Account.objects.filter(wallet__isnull=False).count()
accounts_without_wallets = Account.objects.filter(wallet__isnull=True).count()

print(f"\n?? FINAL VERIFICATION:")
print(f"  Total accounts: {total_accounts}")
print(f"  Accounts with wallets: {accounts_with_wallets}")
print(f"  Accounts without wallets: {accounts_without_wallets}")

if accounts_without_wallets == 0:
    print("\n? ALL ACCOUNTS NOW HAVE WALLETS!")
    print("   System is fully ready for Payments and Transfers apps.")
else:
    print(f"\n??  Still {accounts_without_wallets} accounts without wallets.")

print("\n" + "=" * 70)
