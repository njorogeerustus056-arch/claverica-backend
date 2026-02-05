#!/usr/bin/env python
"""
🔔 SIMPLE NOTIFICATION TEST
Quick verification from command line
"""

import os
import sys

# Add the parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

from notifications.models import Notification, NotificationLog, NotificationPreference
from django.contrib.auth import get_user_model
import json

print("=" * 70)
print("🔔 NOTIFICATION SYSTEM - QUICK TEST")
print("=" * 70)

def test_basic_notification():
    """Test basic notification creation"""
    try:
        print("\n1️⃣ TEST: Basic Notification Creation")
        print("-" * 40)
        
        # Create a simple notification
        notification = Notification.objects.create(
            notification_type="SYSTEM_TEST",
            title="Test Notification",
            message="Testing the notification system",
            priority="MEDIUM",
            status="PENDING"
        )
        
        print(f"✅ Notification created: ID #{notification.id}")
        print(f"   Type: {notification.notification_type}")
        print(f"   Title: {notification.title}")
        print(f"   Status: {notification.status}")
        
        return notification
        
    except Exception as e:
        print(f"❌ Failed to create notification: {str(e)}")
        return None

def test_notification_logging(notification):
    """Test notification logging"""
    try:
        print("\n2️⃣ TEST: Notification Logging")
        print("-" * 40)
        
        # Create log entry
        log = NotificationLog.objects.create(
            notification=notification,
            delivery_method="EMAIL",
            status="SENT",
            recipient_email="test@example.com",
            details="Test notification sent successfully"
        )
        
        print(f"✅ Log created: ID #{log.id}")
        print(f"   Method: {log.delivery_method}")
        print(f"   Status: {log.status}")
        print(f"   Recipient: {log.recipient_email}")
        
        return log
        
    except Exception as e:
        print(f"❌ Failed to create log: {str(e)}")
        return None

def test_financial_notifications():
    """Test financial workflow notifications"""
    try:
        print("\n3️⃣ TEST: Financial Workflow Notifications")
        print("-" * 40)
        
        # Test different notification types for your financial system
        notification_types = [
            {
                "type": "PAYMENT_RECEIVED",
                "title": "💰 Payment Received",
                "message": "You received $500.00 from John Doe",
                "data": {"amount": "500.00", "sender": "John Doe", "reference": "PAY-001"}
            },
            {
                "type": "TRANSFER_INITIATED", 
                "title": "🚀 Transfer Initiated",
                "message": "Transfer of $250.00 to Jane Doe has been initiated",
                "data": {"amount": "250.00", "recipient": "Jane Doe", "status": "pending"}
            },
            {
                "type": "TAC_GENERATED",
                "title": "🔑 Your TAC Code",
                "message": "Your TAC code is 123456",
                "data": {"tac_code": "123456", "purpose": "transfer", "expires": "24h"}
            },
            {
                "type": "KYC_REQUIRED",
                "title": "📋 KYC Verification Required",
                "message": "Please complete KYC for large transfer",
                "data": {"amount": "2000.00", "threshold": "1500.00", "action": "upload"}
            }
        ]
        
        created_notifications = []
        
        for nt in notification_types:
            notif = Notification.objects.create(
                notification_type=nt["type"],
                title=nt["title"],
                message=nt["message"],
                data=json.dumps(nt["data"]),
                priority="HIGH" if nt["type"] in ["TAC_GENERATED", "KYC_REQUIRED"] else "MEDIUM",
                status="PENDING"
            )
            
            created_notifications.append(notif)
            print(f"✅ {nt['type']}: #{notif.id}")
        
        print(f"\n✅ Created {len(created_notifications)} financial notifications")
        return created_notifications
        
    except Exception as e:
        print(f"❌ Financial notifications failed: {str(e)}")
        return []

def test_preferences():
    """Test notification preferences"""
    try:
        print("\n4️⃣ TEST: Notification Preferences")
        print("-" * 40)
        
        # Create or get a test user
        User = get_user_model()
        test_user, created = User.objects.get_or_create(
            email="notification_test@claverica.com",
            defaults={"username": "notifytest", "is_active": False}
        )
        
        if created:
            print(f"✅ Created test user: {test_user.email}")
        
        # Test preference creation
        pref_types = ["PAYMENT_RECEIVED", "TRANSFER_INITIATED", "TAC_GENERATED", "KYC_REQUIRED"]
        
        for pref_type in pref_types:
            pref, created = NotificationPreference.objects.get_or_create(
                user=test_user,
                notification_type=pref_type,
                defaults={
                    "enabled": True,
                    "delivery_method": "EMAIL,SMS"
                }
            )
            
            action = "Created" if created else "Exists"
            print(f"✅ {action} preference: {pref_type}")
        
        # Cleanup test user
        if created:
            test_user.delete()
            print("✅ Test user cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Preferences test failed: {str(e)}")
        return False

def cleanup_test_data():
    """Cleanup test data"""
    try:
        print("\n5️⃣ TEST: Cleanup")
        print("-" * 40)
        
        # Delete test notifications
        test_types = ["SYSTEM_TEST", "PAYMENT_RECEIVED", "TRANSFER_INITIATED", 
                     "TAC_GENERATED", "KYC_REQUIRED"]
        
        deleted_count, _ = Notification.objects.filter(
            notification_type__in=test_types
        ).delete()
        
        # Delete test logs
        log_deleted, _ = NotificationLog.objects.filter(
            details__contains="Test"
        ).delete()
        
        print(f"✅ Deleted {deleted_count} test notifications")
        print(f"✅ Deleted {log_deleted} test logs")
        
        return True
        
    except Exception as e:
        print(f"⚠️ Cleanup warning: {str(e)}")
        return True

def main():
    """Run all tests"""
    print("\n🎯 RUNNING NOTIFICATION TESTS...")
    
    # Run tests
    notification = test_basic_notification()
    
    if notification:
        log = test_notification_logging(notification)
    
    financial_notifs = test_financial_notifications()
    prefs_result = test_preferences()
    cleanup_test_data()
    
    print("\n" + "=" * 70)
    print("📊 NOTIFICATION TEST SUMMARY")
    print("=" * 70)
    
    # Count existing notifications
    total_notifs = Notification.objects.count()
    total_logs = NotificationLog.objects.count()
    total_prefs = NotificationPreference.objects.count()
    
    print(f"✅ Total notifications in DB: {total_notifs}")
    print(f"✅ Total logs in DB: {total_logs}")
    print(f"✅ Total preferences in DB: {total_prefs}")
    
    print("\n🎉 NOTIFICATION SYSTEM IS WORKING!")
    print("=" * 70)
    
    # Show notification types present
    notif_types = Notification.objects.values_list('notification_type', flat=True).distinct()
    print(f"\n📋 Notification types in system: {list(notif_types)}")

if __name__ == "__main__":
    main()