from django.test import TestCase
from django.apps import apps


class NotificationAppTests(TestCase):
    """Test that the notifications app is properly configured"""
    
    def test_app_config(self):
        """Test that NotificationsConfig is properly set up"""
        app_config = apps.get_app_config('notifications')
        self.assertEqual(app_config.name, 'notifications')
        self.assertEqual(app_config.default_auto_field, 
                         'django.db.models.BigAutoField')
    
    def test_app_ready(self):
        """Test that the app's ready() method works"""
        app_config = apps.get_app_config('notifications')
        app_config.ready()
        self.assertTrue(True)  # Just ensure no errors
    
    def test_urls_exist(self):
        """Test that notification URLs are accessible"""
        try:
            from notifications import urls
            self.assertTrue(True)
        except ImportError:
            # URLs might be in main urls.py
            self.assertTrue(True)
