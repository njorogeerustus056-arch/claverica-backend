import os
import sys
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from accounts.models import Account
from transactions.models import Wallet

print("=" * 60)
print("?? ENSURING ALL ACCOUNTS HAVE WALLETS")
print("=" * 60)

# Get all accounts
all_accounts = Account.objects.all()
print(f"Found {all_accounts.count()} total accounts")

# Count accounts with/without wallets
accounts_with_wallets = Account.objects.filter(wallet__isnull=False)
accounts_without_wallets = Account.objects.filter(wallet__isnull=True)

print(f"Accounts with wallets: {accounts_with_wallets.count()}")
print(f"Accounts without wallets: {accounts_without_wallets.count()}")

if accounts_without_wallets.count() > 0:
    print("\n?? Creating wallets for accounts without them...")
    for account in accounts_without_wallets:
        wallet = Wallet.objects.create(
            account=account,
            balance=0.00,
            currency='USD'
        )
        print(f"  ? Created wallet for {account.email}: {wallet.id}")
    print(f"\n?? Created {accounts_without_wallets.count()} new wallets!")
else:
    print("\n?? All accounts already have wallets!")

# Final count
print(f"\n?? FINAL COUNT:")
print(f"  Total accounts: {Account.objects.count()}")
print(f"  Accounts with wallets: {Account.objects.filter(wallet__isnull=False).count()}")
print(f"  Accounts without wallets: {Account.objects.filter(wallet__isnull=True).count()}")

print("\n" + "=" * 60)
print("? WALLET FIX COMPLETE")
