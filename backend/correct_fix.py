import os
import django
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
django.setup()

from accounts.models import Account
from users.models import UserProfile, UserSettings
from transactions.models import Wallet

print("=== CORRECT LEGACY ACCOUNT FIX ===")

# First, check UserProfile structure
print("\n1. Checking UserProfile structure...")
profile_fields = [f.name for f in UserProfile._meta.fields]
print(f"   UserProfile fields: {profile_fields}")

# Check what minimal fields UserProfile needs
print("\n2. Fixing legacy accounts...")
fixed_count = 0

for account in Account.objects.all():
    account_fixed = False
    
    # Fix UserProfile - only pass fields that UserProfile actually has
    if not hasattr(account, 'user_profile'):
        try:
            # Minimal UserProfile creation
            profile_data = {'account': account}
            
            # Only add fields that exist in UserProfile
            if 'bio' in profile_fields:
                profile_data['bio'] = ""
            if 'avatar' in profile_fields:
                profile_data['avatar'] = None
            if 'email_notifications' in profile_fields:
                profile_data['email_notifications'] = True
            
            UserProfile.objects.create(**profile_data)
            fixed_count += 1
            account_fixed = True
            print(f"  ✅ Created UserProfile for {account.email}")
        except Exception as e:
            print(f"  ❌ Error creating UserProfile for {account.email}: {str(e)}")
    
    # Fix UserSettings
    if not hasattr(account, 'user_settings'):
        try:
            UserSettings.objects.create(account=account)
            fixed_count += 1
            account_fixed = True
            print(f"  ✅ Created UserSettings for {account.email}")
        except Exception as e:
            print(f"  ❌ Error creating UserSettings for {account.email}: {str(e)}")
    
    # Fix Wallet (if missing)
    if not Wallet.objects.filter(account=account).exists():
        try:
            Wallet.objects.create(
                account=account,
                currency='USD',
                balance=0.00
            )
            fixed_count += 1
            account_fixed = True
            print(f"  ✅ Created Wallet for {account.email}")
        except Exception as e:
            print(f"  ❌ Error creating Wallet for {account.email}: {str(e)}")

print(f"\n✅ Created {fixed_count} missing components")

# Verify all accounts
print("\n3. Verification:")
all_good = True
for account in Account.objects.all():
    has_profile = hasattr(account, 'user_profile')
    has_settings = hasattr(account, 'user_settings')
    has_wallet = Wallet.objects.filter(account=account).exists()
    
    if not (has_profile and has_settings and has_wallet):
        print(f"  ❌ {account.email}: Profile={has_profile}, Settings={has_settings}, Wallet={has_wallet}")
        all_good = False
    else:
        print(f"  ✅ {account.email}: Complete")

if all_good:
    print("\n🎉 ALL ACCOUNTS ARE NOW COMPLETE!")
else:
    print("\n⚠️  Some accounts still need attention")

# Check counts
print("\n4. Final Counts:")
print(f"   Accounts: {Account.objects.count()}")
print(f"   UserProfiles: {UserProfile.objects.count()}")
print(f"   UserSettings: {UserSettings.objects.count()}")
print(f"   Wallets: {Wallet.objects.count()}")
