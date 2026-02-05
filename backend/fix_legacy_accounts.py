import os
import django
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
django.setup()

from accounts.models import Account
from users.models import UserProfile, UserSettings
from transactions.models import Wallet

print("=== COMPREHENSIVE DATABASE FIX ===")

# Part 1: Fix legacy accounts
print("\n1. Fixing legacy accounts...")
fixed_components = 0

for account in Account.objects.all():
    account_fixed = False
    
    # Fix UserProfile
    if not hasattr(account, 'user_profile'):
        UserProfile.objects.create(
            account=account,
            first_name=account.first_name or "",
            last_name=account.last_name or "",
            phone=account.phone or "",
            date_of_birth=account.date_of_birth,
            gender=account.gender,
            doc_type=getattr(account, 'doc_type', ''),
            doc_number=getattr(account, 'doc_number', ''),
            address_line1=getattr(account, 'address_line1', ''),
            city=getattr(account, 'city', ''),
            state_province=getattr(account, 'state_province', ''),
            postal_code=getattr(account, 'postal_code', ''),
            country=getattr(account, 'country', ''),
            doc_country=getattr(account, 'doc_country', ''),
            country_of_residence=getattr(account, 'country_of_residence', ''),
            nationality=getattr(account, 'nationality', '')
        )
        fixed_components += 1
        account_fixed = True
    
    # Fix UserSettings
    if not hasattr(account, 'user_settings'):
        UserSettings.objects.create(account=account)
        fixed_components += 1
        account_fixed = True
    
    # Fix Wallet (if missing)
    if not Wallet.objects.filter(account=account).exists():
        Wallet.objects.create(
            account=account,
            currency='USD',
            balance=0.00
        )
        fixed_components += 1
        account_fixed = True
    
    if account_fixed:
        print(f"  Fixed: {account.email}")

print(f"\n✅ Created {fixed_components} missing components")

# Part 2: Verify all accounts
print("\n2. Verifying all accounts...")
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

# Part 3: Check Wallet foreign keys
print("\n3. Checking Wallet relationships...")
for wallet in Wallet.objects.all():
    try:
        # Try to access the related account
        account = wallet.account
        print(f"  ✅ Wallet {wallet.id}: Linked to {account.email}")
    except Exception as e:
        print(f"  ❌ Wallet {wallet.id}: Error - {str(e)}")

if all_good:
    print("\n🎉 ALL ACCOUNTS ARE NOW COMPLETE!")
    print("   Every account has:")
    print("   - UserProfile")
    print("   - UserSettings") 
    print("   - Wallet")
else:
    print("\n⚠️  Some accounts still need attention")
