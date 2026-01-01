"""
notifications/tests.py - FIXED VERSION
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from notifications.models import (
    Notification, 
    NotificationPreference, 
    NotificationTemplate,
    NotificationDevice
)
import uuid
from django.utils import timezone

User = get_user_model()


class NotificationModelTests(TestCase):
    """Test cases for Notification model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_create_notification(self):
        """Test creating a notification"""
        notification = Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='This is a test notification',
            notification_type='transaction'
        )
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.title, 'Test Notification')
        self.assertEqual(notification.notification_type, 'transaction')
    
    def test_mark_as_read(self):
        """Test marking notification as read"""
        notification = Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='This is a test notification',
            notification_type='transaction'
        )
        self.assertFalse(notification.is_read)
        
        notification.mark_as_read()
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)
    
    def test_mark_as_unread(self):
        """Test marking notification as unread"""
        notification = Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='This is a test notification',
            notification_type='transaction'
        )
        notification.mark_as_read()
        self.assertTrue(notification.is_read)
        
        notification.mark_as_unread()
        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.read_at)
    
    def test_notification_priority_choices(self):
        """Test notification priority choices"""
        notification = Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='This is a test notification',
            notification_type='transaction',
            priority='high'
        )
        self.assertEqual(notification.priority, 'high')
    
    def test_notification_str_method(self):
        """Test string representation of notification"""
        notification = Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='This is a test notification',
            notification_type='transaction'
        )
        # Fixed: Updated to match the actual __str__ method format
        self.assertEqual(str(notification), f"{self.user.email} - Test Notification")
    
    def test_time_ago_property(self):
        """Test time_ago property"""
        notification = Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='This is a test notification',
            notification_type='transaction'
        )
        self.assertIsNotNone(notification.time_ago)
    
    def test_archive_method(self):
        """Test archiving notification"""
        notification = Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='This is a test notification',
            notification_type='transaction'
        )
        self.assertFalse(notification.is_archived)
        
        notification.archive()
        self.assertTrue(notification.is_archived)


class NotificationPreferenceTests(TestCase):
    """Test cases for NotificationPreference model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='preference_test@example.com',
            password='testpass123',
            first_name='Preference',
            last_name='Test'
        )
    
    def test_default_preferences(self):
        """Test that default preferences are created correctly"""
        # Check if preferences were created by signal
        preferences = NotificationPreference.objects.filter(user=self.user)
        self.assertTrue(preferences.exists())
        
        # Check default values
        preference = preferences.first()
        self.assertTrue(preference.in_app_enabled)
        self.assertTrue(preference.email_enabled)
        self.assertFalse(preference.sms_enabled)
        self.assertTrue(preference.push_enabled)
        self.assertTrue(preference.transaction_notifications)
        self.assertTrue(preference.security_notifications)
    
    def test_preference_creation_with_custom_values(self):
        """Test creating preferences with custom values"""
        # Delete existing preference if exists
        NotificationPreference.objects.filter(user=self.user).delete()
        
        preference = NotificationPreference.objects.create(
            user=self.user,
            email_enabled=False,
            push_enabled=True,
            in_app_enabled=False,
            sms_enabled=True
        )
        self.assertFalse(preference.email_enabled)
        self.assertTrue(preference.push_enabled)
        self.assertFalse(preference.in_app_enabled)
        self.assertTrue(preference.sms_enabled)
    
    def test_preference_str_method(self):
        """Test string representation of preference"""
        preference = NotificationPreference.objects.get(user=self.user)
        self.assertEqual(str(preference), f"{self.user.email}'s Notification Preferences")
    
    def test_preference_update(self):
        """Test updating preferences"""
        preference = NotificationPreference.objects.get(user=self.user)
        preference.transaction_notifications = False
        preference.save()
        
        updated = NotificationPreference.objects.get(user=self.user)
        self.assertFalse(updated.transaction_notifications)


class NotificationTemplateTests(TestCase):
    """Test cases for NotificationTemplate model"""
    
    def test_template_creation(self):
        """Test creating a notification template"""
        template = NotificationTemplate.objects.create(
            template_type='transaction_success',
            title_template='Transaction Successful: {amount}',
            message_template='Your transaction of {amount} to {recipient} was successful.',
            notification_type='transaction',
            priority='medium'
        )
        self.assertEqual(template.template_type, 'transaction_success')
        self.assertEqual(template.title_template, 'Transaction Successful: {amount}')
        self.assertEqual(template.notification_type, 'transaction')
    
    def test_template_str_method(self):
        """Test string representation of template"""
        template = NotificationTemplate.objects.create(
            template_type='password_changed',
            title_template='Password Changed',
            message_template='Your password was successfully changed.',
            notification_type='security',
            priority='high'
        )
        # Check string representation
        self.assertEqual(str(template), f"Template: {template.get_template_type_display()}")
    
    def test_template_render(self):
        """Test rendering template with context"""
        template = NotificationTemplate.objects.create(
            template_type='payment_received',
            title_template='Payment Received: {amount}',
            message_template='You received {amount} from {sender}.',
            notification_type='payment',
            priority='medium'
        )
        
        context = {'amount': '$100', 'sender': 'John Doe'}
        rendered = template.render(context)
        
        self.assertEqual(rendered['title'], 'Payment Received: $100')
        self.assertEqual(rendered['message'], 'You received $100 from John Doe.')
        self.assertEqual(rendered['notification_type'], 'payment')
        self.assertEqual(rendered['priority'], 'medium')
    
    def test_template_render_missing_context(self):
        """Test rendering template with missing context variables"""
        template = NotificationTemplate.objects.create(
            template_type='test_template',
            title_template='Test: {name}',
            message_template='Hello {name}, you have {count} notifications.',
            notification_type='system',
            priority='low'
        )
        
        # Test with incomplete context
        rendered = template.render({'name': 'Alice'})
        
        # Title should work because {name} is in context
        self.assertEqual(rendered['title'], 'Test: Alice')
        
        # Message should return original template because {count} is missing
        # The render() method catches KeyError and returns the original template
        self.assertEqual(rendered['message'], 'Hello {name}, you have {count} notifications.')
        
        # Test with complete context to verify it works when all variables are provided
        rendered = template.render({'name': 'Alice', 'count': 5})
        self.assertEqual(rendered['title'], 'Test: Alice')
        self.assertEqual(rendered['message'], 'Hello Alice, you have 5 notifications.')


class NotificationDeviceTests(TestCase):
    """Test cases for NotificationDevice model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='device_test@example.com',
            password='testpass123',
            first_name='Device',
            last_name='Test'
        )
    
    def test_device_creation(self):
        """Test creating a notification device"""
        device = NotificationDevice.objects.create(
            user=self.user,
            device_type='ios',
            device_token='test-device-token-123',
            device_name='iPhone 13'
        )
        self.assertEqual(device.user, self.user)
        self.assertEqual(device.device_type, 'ios')
        self.assertEqual(device.device_token, 'test-device-token-123')
        self.assertTrue(device.is_active)
    
    def test_device_str_method(self):
        """Test string representation of device"""
        device = NotificationDevice.objects.create(
            user=self.user,
            device_type='android',
            device_token='test-android-token',
            device_name='Samsung Galaxy'
        )
        expected = f"{self.user.email} - android - Samsung Galaxy"
        self.assertEqual(str(device), expected)
    
    def test_device_without_name(self):
        """Test device without name"""
        device = NotificationDevice.objects.create(
            user=self.user,
            device_type='web',
            device_token='test-web-token'
        )
        expected = f"{self.user.email} - web - Unnamed"
        self.assertEqual(str(device), expected)


class NotificationManagerTests(TestCase):
    """Test cases for Notification manager/queryset methods"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='manager_test@example.com',
            password='testpass123',
            first_name='Manager',
            last_name='Test'
        )
        
        # Create some notifications
        self.notification1 = Notification.objects.create(
            user=self.user,
            title='Notification 1',
            message='Message 1',
            notification_type='transaction',
            is_read=False
        )
        self.notification2 = Notification.objects.create(
            user=self.user,
            title='Notification 2',
            message='Message 2',
            notification_type='security',
            is_read=True
        )
        self.notification3 = Notification.objects.create(
            user=self.user,
            title='Notification 3',
            message='Message 3',
            notification_type='account',
            is_read=False
        )
        # Create an archived notification
        self.notification4 = Notification.objects.create(
            user=self.user,
            title='Notification 4',
            message='Message 4',
            notification_type='promotion',
            is_read=False,
            is_archived=True
        )
    
    def test_unread_count(self):
        """Test counting unread notifications"""
        unread_count = Notification.objects.filter(user=self.user, is_read=False, is_archived=False).count()
        self.assertEqual(unread_count, 2)
    
    def test_mark_all_as_read(self):
        """Test marking all notifications as read for a user"""
        # Mark all non-archived as read
        updated_count = Notification.objects.filter(user=self.user, is_read=False, is_archived=False).update(
            is_read=True, read_at=timezone.now()
        )
        
        # Check all are read
        unread_count = Notification.objects.filter(user=self.user, is_read=False, is_archived=False).count()
        self.assertEqual(unread_count, 0)
        self.assertEqual(updated_count, 2)
    
    def test_archived_notifications(self):
        """Test handling of archived notifications"""
        archived_count = Notification.objects.filter(user=self.user, is_archived=True).count()
        self.assertEqual(archived_count, 1)


class NotificationIntegrationTests(TestCase):
    """Integration tests for notifications"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='integration_test@example.com',
            password='testpass123',
            first_name='Integration',
            last_name='Test'
        )
    
    def test_create_notification_from_template(self):
        """Test creating a notification using a template"""
        # Create a template
        template = NotificationTemplate.objects.create(
            template_type='test_integration',
            title_template='Integration Test: {test_name}',
            message_template='This is an integration test for {test_name}.',
            notification_type='system',
            priority='medium'
        )
        
        # Create notification using template
        context = {'test_name': 'Notification System'}
        rendered = template.render(context)
        
        notification = Notification.objects.create(
            user=self.user,
            title=rendered['title'],
            message=rendered['message'],
            notification_type=rendered['notification_type'],
            priority=rendered['priority']
        )
        
        self.assertEqual(notification.title, 'Integration Test: Notification System')
        self.assertEqual(notification.notification_type, 'system')
    
    def test_user_preference_filtering(self):
        """Test that notifications respect user preferences"""
        # Get user preferences
        preference = NotificationPreference.objects.get(user=self.user)
        
        # Disable some notifications
        preference.transaction_notifications = False
        preference.promotional_notifications = False
        preference.save()
        
        # Create notifications
        transaction_notification = Notification.objects.create(
            user=self.user,
            title='Transaction Test',
            message='Testing transaction notifications',
            notification_type='transaction'
        )
        
        promo_notification = Notification.objects.create(
            user=self.user,
            title='Promotion Test',
            message='Testing promotional notifications',
            notification_type='promotion'
        )
        
        security_notification = Notification.objects.create(
            user=self.user,
            title='Security Test',
            message='Testing security notifications',
            notification_type='security'
        )
        
        # All notifications should still be created regardless of preferences
        # Preferences are for delivery channels, not creation
        notifications_count = Notification.objects.filter(user=self.user).count()
        self.assertEqual(notifications_count, 3)
    
    def test_notification_with_metadata(self):
        """Test notification with metadata"""
        metadata = {
            'transaction_id': str(uuid.uuid4()),
            'amount': 100.50,
            'currency': 'USD',
            'timestamp': timezone.now().isoformat()
        }
        
        notification = Notification.objects.create(
            user=self.user,
            title='Transaction with Metadata',
            message='This notification includes metadata',
            notification_type='transaction',
            metadata=metadata
        )
        
        self.assertEqual(notification.metadata['amount'], 100.50)
        self.assertEqual(notification.metadata['currency'], 'USD')
    
    def test_notification_expiry(self):
        """Test notification expiry field"""
        future_time = timezone.now() + timezone.timedelta(days=7)
        
        notification = Notification.objects.create(
            user=self.user,
            title='Expiring Notification',
            message='This notification will expire',
            notification_type='system',
            expires_at=future_time
        )
        
        self.assertIsNotNone(notification.expires_at)
        self.assertGreater(notification.expires_at, timezone.now())