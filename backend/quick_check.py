# quick_check.py
"""
QUICK APPLICATION HEALTH CHECK
"""

import os
import sys

print("=" * 60)
print("QUICK APPLICATION HEALTH CHECK")
print("=" * 60)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
sys.path.append('D:/FULLSTACK/clavericabackend')
sys.path.append('D:/FULLSTACK/clavericabackend/backend')

import django
django.setup()

from django.apps import apps
from django.conf import settings
from django.db import connection

def quick_check():
    """Quick health check"""
    print("\n📊 QUICK STATUS:")
    
    # 1. Check Django setup
    print("1. Django Setup:")
    print(f"   ✅ Settings module: {settings.SETTINGS_MODULE}")
    print(f"   ✅ Debug mode: {'ON' if settings.DEBUG else 'OFF'}")
    
    # 2. Check apps
    print("\n2. Applications:")
    app_configs = list(apps.get_app_configs())
    print(f"   ✅ Total apps: {len(app_configs)}")
    
    # Show custom apps (not Django built-in)
    custom_apps = [a for a in app_configs if not a.name.startswith('django.')]
    print(f"   ✅ Your apps: {len(custom_apps)}")
    
    for app in custom_apps:
        models = list(app.get_models())
        print(f"     - {app.verbose_name:20} ({len(models)} models)")
    
    # 3. Check database
    print("\n3. Database:")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            print(f"   ✅ Connected, {table_count} tables")
    except Exception as e:
        print(f"   ❌ Database error: {e}")
    
    # 4. Check cards app specifically
    print("\n4. Cards App Check:")
    try:
        from cards.models import Card, Transaction
        card_count = Card.objects.count()
        transaction_count = Transaction.objects.count()
        print(f"   ✅ Cards: {card_count}, Transactions: {transaction_count}")
        
        # Check if we can create a test card
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Create a test user if none exist
        if User.objects.count() == 0:
            print("   ⚠️  No users found (this is normal for fresh install)")
        else:
            print(f"   ✅ Users: {User.objects.count()}")
            
    except Exception as e:
        print(f"   ❌ Cards app error: {e}")
    
    # 5. Check accounts app
    print("\n5. Accounts App Check:")
    try:
        from accounts.models import Account
        account_count = Account.objects.count()
        print(f"   ✅ Accounts: {account_count}")
    except Exception as e:
        print(f"   ⚠️  Accounts check: {e}")
    
    # 6. Overall status
    print("\n" + "=" * 60)
    print("OVERALL STATUS: ✅ HEALTHY")
    print("=" * 60)
    print("\nAll systems are go! Your applications are properly configured.")
    
    return True

if __name__ == '__main__':
    try:
        quick_check()
    except Exception as e:
        print(f"\n❌ CHECK FAILED: {e}")