import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clavera.settings')
django.setup()

from django.db import connection, migrations, models
import django.db.models.deletion

print("🔧 Creating migration operations for missing columns...")

# Define the migration operations
operations = [
    # transfers_transferrequest.amount
    migrations.AddField(
        model_name='transferrequest',
        name='amount',
        field=models.DecimalField(
            max_digits=15,
            decimal_places=2,
            default=0.00,
            blank=True,
            null=True
        ),
    ),
    
    # transactions_transaction.transaction_type
    migrations.AddField(
        model_name='transaction',
        name='transaction_type',
        field=models.CharField(
            max_length=50,
            default='transfer',
            blank=True,
            null=True
        ),
    ),
    
    # payments_card.expiry_date (if still missing)
    migrations.AddField(
        model_name='card',
        name='expiry_date',
        field=models.DateField(blank=True, null=True),
    ),
    
    # payments_payment.user_id (if still missing)
    migrations.AddField(
        model_name='payment',
        name='user_id',
        field=models.BigIntegerField(blank=True, null=True),
    ),
    
    # payments_transaction.status (if still missing)
    migrations.AddField(
        model_name='transaction',
        name='status',
        field=models.CharField(
            max_length=50,
            default='pending',
            blank=True,
            null=True
        ),
    ),
]

print(f"✅ Created {len(operations)} migration operations")
print("Now run: python manage.py makemigrations && python manage.py migrate")
