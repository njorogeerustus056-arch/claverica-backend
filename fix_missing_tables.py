import sys, os
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()
from django.core.management import execute_from_command_line

print("🔧 FIXING MISSING DATABASE TABLES")
print("=" * 50)

# These are the missing tables based on the error:
# 1. payments_payment
# 2. transfers_transferrequest  
# 3. transfers_transferlimit

print("\n1️⃣  CHECKING MIGRATIONS STATUS:")
try:
    # Check migrations
    execute_from_command_line(['manage.py', 'showmigrations'])
    print("   ✅ Migration system working")
except Exception as e:
    print(f"   ❌ Migration check failed: {str(e)[:100]}")

print("\n2️⃣  CHECKING SPECIFIC APPS:")

# Check payments app
print("\n🔍 Payments App:")
try:
    from django.apps import apps
    payments_app = apps.get_app_config('payments')
    payment_models = list(payments_app.get_models())
    print(f"   Found {len(payment_models)} models in payments")
    
    for model in payment_models:
        try:
            count = model.objects.count()
            print(f"   ✅ {model.__name__}: {count} records")
        except Exception as e:
            print(f"   ❌ {model.__name__}: Table missing - {str(e)[:80]}")
            
            # Try to make migrations
            print(f"   🔄 Attempting to create migration for {model.__name__}...")
            
except Exception as e:
    print(f"   ❌ Payments app error: {str(e)[:100]}")

# Check transfers app  
print("\n🔍 Transfers App:")
try:
    transfers_app = apps.get_app_config('transfers')
    transfer_models = list(transfers_app.get_models())
    print(f"   Found {len(transfer_models)} models in transfers")
    
    for model in transfer_models:
        try:
            count = model.objects.count()
            print(f"   ✅ {model.__name__}: {count} records")
        except Exception as e:
            print(f"   ❌ {model.__name__}: Table missing - {str(e)[:80]}")
            
except Exception as e:
    print(f"   ❌ Transfers app error: {str(e)[:100]}")

print("\n3️⃣  POSSIBLE SOLUTIONS:")
print("""
   Option 1: Run migrations
     python manage.py makemigrations
     python manage.py migrate

   Option 2: If migrations exist but tables don't:
     python manage.py migrate payments --fake
     python manage.py migrate transfers --fake

   Option 3: Drop and recreate (LAST RESORT):
     python manage.py migrate payments zero
     python manage.py migrate transfers zero
     python manage.py migrate payments
     python manage.py migrate transfers
""")

print("\n" + "=" * 50)
print("🔧 RUN THESE COMMANDS TO FIX:")
print("1. python manage.py makemigrations")
print("2. python manage.py migrate")
