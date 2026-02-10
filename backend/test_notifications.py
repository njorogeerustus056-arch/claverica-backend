import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

import django
django.setup()

from django.contrib.auth import get_user_model
from notifications.models import Notification

print("🧪 TESTING NOTIFICATIONS")

User = get_user_model()
user = User.objects.first()

if not user:
    print("❌ No users found!")
    exit()

print(f"👤 Testing with user: {user.email}")

try:
    # Test 1: Create notification
    print("\n1. Creating notification...")
    notification = Notification.objects.create(
        recipient=user,
        title='Test Notification',
        message='This is a test notification',
        notification_type='SYSTEM_ALERT'
    )
    print(f"✅ Created: ID {notification.id}")
    print(f"   Title: {notification.title}")
    print(f"   Type: {notification.notification_type}")
    print(f"   Status: {notification.status}")
    
    # Test 2: Mark as read
    print("\n2. Marking as read...")
    notification.mark_as_read()
    print(f"✅ Marked as read")
    print(f"   New status: {notification.status}")
    
    # Test 3: Count
    print("\n3. Counting notifications...")
    count = Notification.objects.count()
    user_count = Notification.objects.filter(recipient=user).count()
    print(f"✅ Total notifications: {count}")
    print(f"✅ User's notifications: {user_count}")
    
    # Test 4: Create more notifications
    print("\n4. Creating payment notification...")
    payment = Notification.objects.create(
        recipient=user,
        title='Payment Received',
        message='Your account was credited with $500',
        notification_type='PAYMENT_RECEIVED'
    )
    print(f"✅ Created payment notification")
    
    # Test 5: Create transfer notification
    print("\n5. Creating transfer notification...")
    transfer = Notification.objects.create(
        recipient=user,
        title='Transfer Initiated',
        message='Transfer #123 has been initiated',
        notification_type='TRANSFER_INITIATED'
    )
    print(f"✅ Created transfer notification")
    
    # Final count
    final_count = Notification.objects.count()
    print(f"\n📊 FINAL COUNT: {final_count} notifications")
    
    print("\n" + "="*50)
    print("🎉 NOTIFICATION SYSTEM IS WORKING!")
    print("="*50)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
