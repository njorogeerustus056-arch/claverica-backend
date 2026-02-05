# simple_check.py - COMPLETE FIXED VERSION
"""
Simple check of your financial system.
"""

import os
import sys

print("🔍 SIMPLE FINANCIAL SYSTEM CHECK")
print("="*60)

# Use the correct settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

try:
    import django
    django.setup()
    print("✅ Django setup successful")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    print("\n⚠️  Make sure you're in the same directory as manage.py")
    print("   Current directory:", os.getcwd())
    sys.exit(1)

# 1. Check core apps
print("\n📦 CHECKING INSTALLED APPS:")
from django.apps import apps

core_apps = ['accounts', 'transactions', 'payments', 'transfers', 'cards', 'kyc', 'compliance']
installed_apps = [app.label for app in apps.get_app_configs()]

for app in core_apps:
    if app in installed_apps:
        print(f"✅ {app}: INSTALLED")
    else:
        print(f"❌ {app}: MISSING")

# 2. Check Account model
print("\n👤 CHECKING ACCOUNT MODEL:")
try:
    from django.contrib.auth import get_user_model
    Account = get_user_model()
    print(f"✅ Account model: {Account}")
    
    # Check fields
    fields = [f.name for f in Account._meta.fields]
    print(f"✅ Fields found: {len(fields)} fields")
    
    # Look for account_number
    if 'account_number' in fields:
        print("✅ Has account_number field")
    else:
        print("⚠️  Missing account_number field")
        
except Exception as e:
    print(f"❌ Account check failed: {e}")

# 3. Check Wallet model
print("\n💰 CHECKING WALLET MODEL:")
try:
    from transactions.models import Wallet
    print(f"✅ Wallet model: {Wallet}")
    
    # Check fields
    wallet_fields = [f.name for f in Wallet._meta.fields]
    print(f"✅ Wallet fields: {', '.join(wallet_fields)}")
    
    if 'balance' in wallet_fields:
        print("✅ Has balance field")
    else:
        print("❌ Missing balance field")
        
    if 'account' in wallet_fields:
        print("✅ Has account relationship")
    else:
        print("❌ Missing account relationship")
        
except ImportError:
    print("⚠️  Wallet model not found (transactions app may not be installed)")
except Exception as e:
    print(f"❌ Wallet check failed: {e}")

# 4. Check other models
print("\n🔧 CHECKING OTHER CORE MODELS:")

models_to_check = [
    ('payments', 'Payment'),
    ('transfers', 'Transfer'),
    ('transfers', 'TAC'),
    ('cards', 'Card'),
    ('kyc', 'KYCDocument'),
    ('compliance', 'ComplianceSetting'),
]

for app, model_name in models_to_check:
    try:
        module = __import__(f'{app}.models', fromlist=[model_name])
        model = getattr(module, model_name)
        print(f"✅ {app}.{model_name}: FOUND")
    except ImportError:
        print(f"❌ {app}.{model_name}: APP NOT FOUND")
    except AttributeError:
        print(f"⚠️  {app}.{model_name}: MODEL NOT IN MODULE")
    except Exception as e:
        print(f"⚠️  {app}.{model_name}: ERROR - {str(e)[:50]}...")

# Update just the test data section in simple_check.py
# Replace lines 114-137 with:

print("\n🧪 CREATING TEST DATA:")
try:
    from django.contrib.auth import get_user_model
    import random
    Account = get_user_model()
    
    # Generate random account number to avoid duplicates
    random_suffix = str(random.randint(1000, 9999))
    account_number = f"CLV-TEST-010190-26-{random_suffix}"
    
    # Create test account
    test_account = Account.objects.create(
        email=f"test_{random_suffix}@claverica.com",
        account_number=account_number
    )
    print(f"✅ Test account created: {test_account.account_number}")
    
    # Check wallet
    if hasattr(test_account, 'wallet'):
        wallet = test_account.wallet
        print(f"✅ Wallet exists: ${wallet.balance}")
        
        # Test credit
        old_balance = float(wallet.balance)
        wallet.balance = old_balance + 100.0
        wallet.save()
        wallet.refresh_from_db()
        print(f"✅ Wallet credited: ${old_balance} → ${wallet.balance}")
        
        # Test debit
        if wallet.balance >= 50.0:
            wallet.balance -= 50.0
            wallet.save()
            wallet.refresh_from_db()
            print(f"✅ Wallet debited: → ${wallet.balance}")
    else:
        print("⚠️  No wallet found for account")
        
    # Clean up
    test_account.delete()
    print("✅ Test data cleaned up")
    
except Exception as e:
    print(f"❌ Test data creation failed: {e}")
    import traceback
    traceback.print_exc()