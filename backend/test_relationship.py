import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

from accounts.models import Account
from users.models import UserProfile, UserSettings

print("=" * 70)
print("🧪 COMPREHENSIVE ACCOUNTS-USERS RELATIONSHIP TEST")
print("=" * 70)

# Count everything
print(f"\n📊 COUNTS:")
print(f"  Accounts: {Account.objects.count()}")
print(f"  UserProfiles: {UserProfile.objects.count()}")
print(f"  UserSettings: {UserSettings.objects.count()}")

# Test forward relationships
print(f"\n🔗 FORWARD RELATIONSHIPS (Profile -> Account):")
for profile in UserProfile.objects.all():
    print(f"  Profile #{profile.id} -> Account: {profile.account.email}")

# Test reverse relationships
print(f"\n🔗 REVERSE RELATIONSHIPS (Account -> Profile):")
for account in Account.objects.all():
    try:
        profile = account.user_profile  # from related_name
        print(f"  Account {account.email} -> Profile ID: {profile.id}")
    except UserProfile.DoesNotExist:
        print(f"  ❌ Account {account.email} -> NO PROFILE")
    
    try:
        settings = account.user_settings  # from related_name
        print(f"          -> Settings ID: {settings.id}")
    except UserSettings.DoesNotExist:
        print(f"          -> NO SETTINGS")

# Test creating a new account with automatic profile
print(f"\n🧪 TEST: Creating new account...")
new_account = Account.objects.create_user(
    email='test_new@example.com',
    password='Test123!',
    phone='+254733445566',
    date_of_birth='1995-08-15'
)
print(f"  ✅ Account created: {new_account.email}")

# Check if profile was auto-created
try:
    profile = new_account.user_profile
    print(f"  ✅ Profile auto-created: {profile.id}")
except UserProfile.DoesNotExist:
    print(f"  ❌ Profile NOT auto-created")

try:
    settings = new_account.user_settings
    print(f"  ✅ Settings auto-created: {settings.id}")
except UserSettings.DoesNotExist:
    print(f"  ❌ Settings NOT auto-created")

print("=" * 70)
print("🎯 TEST COMPLETE")
print("=" * 70)
