# quick_diagnostic.py
import os
import django
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from payments.models import Account

User = get_user_model()

print("="*60)
print("DIAGNOSTIC: Checking Account Creation")
print("="*60)

# Create a test user
user = User.objects.create_user(
    email="diagnostic@example.com",
    password="test123",
    first_name="Diagnostic",
    last_name="Test"
)

# Check accounts
accounts = Account.objects.filter(user=user)
print(f"\nUser {user.email} has {accounts.count()} account(s):")
for i, acc in enumerate(accounts, 1):
    print(f"{i}. {acc.account_number} - {acc.account_type} - ${acc.balance}")

# Check if quick-transfer would work
checking_accounts = accounts.filter(account_type='checking', is_active=True)
print(f"\nActive checking accounts: {checking_accounts.count()}")
if checking_accounts.count() > 1:
    print("⚠️ PROBLEM: Multiple checking accounts - quick-transfer will fail!")
    print("Solution: Use .first() instead of .get() in quick-transfer view")
elif checking_accounts.count() == 1:
    print("✓ Good: Exactly one checking account")
else:
    print("⚠️ No checking accounts found")