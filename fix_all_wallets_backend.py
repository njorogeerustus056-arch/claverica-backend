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

print("=" * 60)
print("?? WALLET STATUS CHECK")
print("=" * 60)

total = Account.objects.count()
with_wallets = Account.objects.filter(wallet__isnull=False).count()
without_wallets = Account.objects.filter(wallet__isnull=True).count()

print(f"Total accounts: {total}")
print(f"Accounts with wallets: {with_wallets}")
print(f"Accounts without wallets: {without_wallets}")

if without_wallets == 0:
    print("\n?? ALL ACCOUNTS HAVE WALLETS!")
    print("   System is ready for Payments and Transfers apps.")
else:
    print(f"\n??  {without_wallets} accounts need wallets.")
    print("   But new accounts will auto-create wallets via signals.")
    
print("\n" + "=" * 60)
