import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
import django
django.setup()

from transfers.models import TransferLimit

print('=== TRANSFER APP TEST ===')
print(f'Number of TransferLimit records: {TransferLimit.objects.count()}')

# Set default amounts if needed
defaults = {
    'daily': 1000,
    'per_transaction': 500,
    'weekly': 5000,
    'monthly': 20000
}

for limit in TransferLimit.objects.all():
    current = limit.amount
    if current == 0 or current is None:
        limit.amount = defaults.get(limit.limit_type, 1000)
        limit.save()
        print(f'  {limit.limit_type}: Updated from ${current} to ${limit.amount}')
    else:
        print(f'  {limit.limit_type}: ${limit.amount}')

print('\n✅ Transfer app is ready!')
print('\nNow test the Transfer workflow:')
print('1. Create TransferRequest')
print('2. Generate TAC')
print('3. Verify funds deduction')
print('4. Manual external settlement')
