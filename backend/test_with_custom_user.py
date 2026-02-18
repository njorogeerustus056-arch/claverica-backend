import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
import django
django.setup()

print("=== TRANSFER APP TEST WITH CUSTOM USER MODEL ===\n")

from transfers.models import TransferLimit, Transfer, TAC
from decimal import Decimal
import uuid
from django.utils import timezone

# 1. Get the custom user model
from django.contrib.auth import get_user_model
User = get_user_model()
print(f"1. Using custom user model: {User.__name__}")

# 2. Verify TransferLimit 
print("\n2. Transfer Limits:")
for limit in TransferLimit.objects.all():
    print(f"   - {limit.limit_type}: ${limit.amount}")

# 3. Create or get a test user
print("\n3. Setting up test user:")
if User.objects.count() == 0:
    try:
        # Try different ways to create user based on model
        if hasattr(User, 'email'):
            user = User.objects.create_user(
                email='client@test.com',
                password='testpass123'
            )
            print(f"   Created user with email: {user.email}")
        elif hasattr(User, 'username'):
            user = User.objects.create_user(
                username='testclient',
                password='testpass123'
            )
            print(f"   Created user: {user.username}")
        else:
            user = User.objects.create(
                phone_number='+1234567890',
                password='testpass123'
            )
            print(f"   Created user with phone: {user.phone_number}")
    except Exception as e:
        print(f"   Error creating user: {e}")
        user = None
else:
    user = User.objects.first()
    print(f"   Using existing user: {user}")

# 4. Need an Account for the user (check if accounts app has Account model)
print("\n4. Checking accounts...")
try:
    from accounts.models import Account
    if Account.objects.filter(user=user).count() == 0 and user:
        account = Account.objects.create(
            user=user,
            account_number=str(uuid.uuid4())[:12],
            account_type='checking',
            balance=1000.00
        )
        print(f"   Created account: {account.account_number} (Balance: ${account.balance})")
    elif user:
        account = Account.objects.filter(user=user).first()
        print(f"   Using account: {account.account_number} (Balance: ${account.balance})")
    else:
        account = None
        print("   No user available for account")
except Exception as e:
    print(f"    Accounts app issue: {e}")
    account = None

# 5. Create a Transfer
print("\n5. Creating Transfer...")
try:
    if account and user:
        transfer = Transfer.objects.create(
            reference=f"TRF-{uuid.uuid4().hex[:8].upper()}",
            account=account,
            amount=Decimal('250.00'),
            recipient_name='John Smith',
            destination_type='bank',
            destination_details={'bank_name': 'National Bank', 'account_number': '9876543210'},
            status='pending',
            narration='Test transfer to John Smith'
        )
        print(f"    Transfer {transfer.reference} created")
        print(f"   Amount: ${transfer.amount}")
        print(f"   Status: {transfer.status}")
        
        # 6. Create a TAC
        tac = TAC.objects.create(
            transfer=transfer,
            code='123456',
            expires_at=timezone.now() + timezone.timedelta(hours=24),
            status='pending'
        )
        print(f"\n6. TAC {tac.code} created (expires: {tac.expires_at})")
        
        print("\n" + "="*50)
        print(" TRANSFER WORKFLOW READY!")
        print("="*50)
        
    else:
        print("    Cannot create transfer - missing user or account")
        
except Exception as e:
    print(f"    Error: {e}")
    import traceback
    traceback.print_exc()

print("\nCurrent Transfer App Status:")
print(f"   TransferLimit: {TransferLimit.objects.count()} limits")
print(f"   Transfers: {Transfer.objects.count()} transfers")
print(f"   TACs: {TAC.objects.count()} TAC codes")
print(f"   Users: {User.objects.count()} users")
