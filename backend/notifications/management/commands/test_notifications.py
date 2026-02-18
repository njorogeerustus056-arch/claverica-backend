"""
 TEST COMMAND: Test notification system
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from accounts.models import Account
from notifications.services import NotificationService
from notifications.models import Notification

class Command(BaseCommand):
    help = 'Test the notification system'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(' TESTING NOTIFICATION SYSTEM'))
        
        # Create test account if needed
        test_email = "notification_test@claverica.com"
        account, created = Account.objects.get_or_create(
            email=test_email,
            defaults={
                'account_number': 'CLV-TEST-001',
                'first_name': 'Test',
                'last_name': 'User',
                'phone': '+254700000000',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(f" Created test account: {account.account_number}")
        else:
            self.stdout.write(f" Using existing account: {account.account_number}")
        
        # Test 1: Create simple notification
        self.stdout.write("\n1 Testing basic notification creation...")
        notification = NotificationService.create_notification(
            account=account,
            notification_type='ACCOUNT_CREATED',
            title='Test Notification',
            message='This is a test notification from the command line',
            priority='MEDIUM',
            metadata={'test': True, 'timestamp': timezone.now().isoformat()}
        )
        
        if notification:
            self.stdout.write(f" Created notification #{notification.id}")
            self.stdout.write(f"   Title: {notification.title}")
            self.stdout.write(f"   Type: {notification.notification_type}")
            self.stdout.write(f"   Priority: {notification.priority}")
        else:
            self.stdout.write(" Failed to create notification")
        
        # Test 2: Mark as read
        self.stdout.write("\n2 Testing mark as read...")
        if notification:
            success = NotificationService.mark_as_read(notification.id, account)
            if success:
                self.stdout.write(" Successfully marked as read")
                notification.refresh_from_db()
                self.stdout.write(f"   New status: {notification.status}")
            else:
                self.stdout.write(" Failed to mark as read")
        
        # Test 3: Get unread count
        self.stdout.write("\n3 Testing unread count...")
        count = Notification.objects.filter(recipient=account, status='UNREAD').count()
        self.stdout.write(f" Unread notifications: {count}")
        
        # Test 4: Create all notification types
        self.stdout.write("\n4 Testing all notification types...")
        
        notification_types = [
            ('PAYMENT_RECEIVED', ' Payment Received', 'You received $500.00 from John Doe'),
            ('TRANSFER_INITIATED', ' Transfer Initiated', 'Transfer of $250.00 initiated'),
            ('TAC_SENT', ' TAC Sent', 'Your TAC code is 123456'),
            ('TRANSFER_COMPLETED', ' Transfer Completed', 'Transfer completed successfully'),
            ('KYC_SUBMITTED', ' KYC Submitted', 'KYC documents submitted for review'),
            ('KYC_APPROVED', ' KYC Approved', 'Your KYC has been approved'),
        ]
        
        created_count = 0
        for nt_type, title, message in notification_types:
            notif = NotificationService.create_notification(
                account=account,
                notification_type=nt_type,
                title=title,
                message=message,
                priority='HIGH' if nt_type in ['TAC_SENT', 'KYC_APPROVED'] else 'MEDIUM'
            )
            
            if notif:
                created_count += 1
                self.stdout.write(f" Created {nt_type}")
            else:
                self.stdout.write(f" Failed {nt_type}")
        
        self.stdout.write(f"\n Created {created_count}/{len(notification_types)} notification types")
        
        # Test 5: Admin notifications
        self.stdout.write("\n5 Testing admin notifications...")
        admin_accounts = Account.objects.filter(is_staff=True)
        if admin_accounts.exists():
            admin_account = admin_accounts.first()
            
            admin_notif = NotificationService.create_notification(
                account=admin_account,
                notification_type='ADMIN_TAC_REQUIRED',
                title=' TAC Required (Admin)',
                message='Generate TAC for transfer CLV-TRF-001',
                priority='HIGH',
                metadata={
                    'admin_action_required': True,
                    'transfer_reference': 'CLV-TRF-001',
                    'amount': '1500.00',
                    'action_url': '/admin/compliance/'
                }
            )
            
            if admin_notif:
                self.stdout.write(f" Created admin notification for {admin_account.account_number}")
            else:
                self.stdout.write(" Failed to create admin notification")
        else:
            self.stdout.write(" No admin account found")
        
        # Test 6: Cleanup old notifications
        self.stdout.write("\n6 Testing cleanup...")
        
        # Create an old notification
        old_notif = Notification.objects.create(
            recipient=account,
            notification_type='SYSTEM_TEST',
            title='Old Notification',
            message='This should be cleaned up',
            priority='LOW',
            status='READ',
            created_at=timezone.now() - timedelta(days=35)
        )
        
        self.stdout.write(f" Created old notification #{old_notif.id}")
        
        # Cleanup
        cleaned_count = NotificationService.cleanup_old_notifications(days=30)
        self.stdout.write(f" Cleaned up {cleaned_count} old notifications")
        
        # Final summary
        total_notifs = Notification.objects.count()
        total_unread = Notification.objects.filter(status='UNREAD').count()
        
        self.stdout.write("\n" + "="*50)
        self.stdout.write(" FINAL NOTIFICATION SYSTEM STATUS:")
        self.stdout.write(f"   Total notifications: {total_notifs}")
        self.stdout.write(f"   Unread notifications: {total_unread}")
        self.stdout.write(f"   Test account: {account.account_number}")
        
        # List notification types
        types = Notification.objects.values_list('notification_type', flat=True).distinct()
        self.stdout.write(f"   Notification types in system: {', '.join(types)}")
        
        self.stdout.write("="*50)
        self.stdout.write(self.style.SUCCESS(' NOTIFICATION SYSTEM TEST COMPLETE'))