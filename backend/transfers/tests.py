"""
Minimal tests for transfers app
"""
from django.test import TestCase


class SimpleTest(TestCase):
    """Simple test to verify test setup works"""
    
    def test_basic_math(self):
        """Test that 1+1=2"""
        self.assertEqual(1 + 1, 2)
    
    def test_transfers_app_exists(self):
        """Test that transfers app is accessible"""
        try:
            from backend.transfers import models
            self.assertTrue(True)
        except ImportError:
            self.fail("Could not import transfers models")
    
    def test_transfer_model_exists(self):
        """Test that Transfer model exists"""
        try:
            from backend.transfers.models import Transfer
            count = Transfer.objects.count()
            # Just check that we can access it
            self.assertTrue(count >= 0)
        except Exception as e:
            self.fail(f"Could not access Transfer model: {e}")
