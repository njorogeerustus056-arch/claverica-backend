import os, sys, django, time
from decimal import Decimal

sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from accounts.models import Account
from transactions.services import WalletService

print("=" * 70)
print("? FINAL SYSTEM VERIFICATION")
print("=" * 70)

# Create test account
t = int(time.time())
email = f"final_verify_{t}@example.com"
phone = f"123{t}"[:20]

print(f"\n1. Creating test account...")
acc = Account.objects.create(
    email=email,
    phone=phone,
    date_of_birth='1990-01-01',
    first_name='Final',
    last_name='Verify'
)
print(f"   Account#: {acc.account_number}")

print(f"\n2. Testing WalletService...")
account_num = acc.account_number

# Test 1: Initial balance
balance = WalletService.get_balance(account_num)
print(f"   Initial balance: ${balance}")

# Test 2: Credit (like Payments app)
new_bal = WalletService.credit_wallet(account_num, Decimal('2500.00'), "TEST-001", "Test payment")
print(f"   After credit $2500: ${new_bal}")

# Test 3: Debit (like Transfers app)
new_bal = WalletService.debit_wallet(account_num, Decimal('750.25'), "TEST-002", "Test transfer")
print(f"   After debit $750.25: ${new_bal}")

# Test 4: History
history = WalletService.get_transaction_history(account_num)
print(f"\n3. Transaction History ({len(history)} records):")

total_in = sum(tx.amount for tx in history if tx.transaction_type == 'payment_in')
total_out = sum(tx.amount for tx in history if tx.transaction_type == 'transfer_out')
print(f"   Total received: ${total_in}")
print(f"   Total sent: ${total_out}")
print(f"   Net: ${total_in - total_out}")
print(f"   Current balance matches: ${new_bal == (total_in - total_out)}")

print(f"\n" + "=" * 70)
print("?? SYSTEM VERIFICATION COMPLETE")
print(f"Account#: {account_num}")
print(f"Final Balance: ${new_bal}")
print("=" * 70)
