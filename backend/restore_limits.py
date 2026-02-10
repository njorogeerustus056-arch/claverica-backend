import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
import django
django.setup()

from transfers.models import TransferLimit

# Restore the limits (they were empty before)
default_limits = [
    {'limit_type': 'daily', 'amount': 1000},
    {'limit_type': 'weekly', 'amount': 5000},
    {'limit_type': 'monthly', 'amount': 20000},
    {'limit_type': 'per_transaction', 'amount': 500}
]

for limit_data in default_limits:
    TransferLimit.objects.get_or_create(
        limit_type=limit_data['limit_type'],
        defaults={'amount': limit_data['amount']}
    )

print('✅ TransferLimit data restored:')
for limit in TransferLimit.objects.all():
    print(f'  {limit.limit_type}: ${limit.amount}')
