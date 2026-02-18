"""
Simple system health check for your financial system.
Run with: python manage.py test tests.test_system_health
"""

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')

import django
django.setup()

from django.test import TestCase
from django.db import connection

class SystemHealthTests(TestCase):
    """Basic health checks for your financial system"""
    
    def test_01_database_connection(self):
        """Test database is accessible"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            self.assertEqual(result, (1,))
            print(" Database connection: ACTIVE")
        except Exception as e:
            self.fail(f" Database connection failed: {e}")
    
    def test_02_core_apps_exist(self):
        """Check if core apps are installed"""
        from django.apps import apps
        
        required_apps = [
            'accounts',
            'transactions', 
            'payments',
            'transfers',
            'cards',
            'kyc',
            'compliance',
        ]
        
        installed_apps = [app.label for app in apps.get_app_configs()]
        
        print("\n Checking installed apps:")
        for app in required_apps:
            if app in installed_apps:
                print(f" {app}: INSTALLED")
            else:
                print(f" {app}: MISSING")
                
        # At least accounts and transactions should exist
        self.assertIn('accounts', installed_apps, "Accounts app is required")
        self.assertIn('transactions', installed_apps, "Transactions app is required")
    
    def test_03_account_model_exists(self):
        """Check if Account model exists"""
        try:
            from django.contrib.auth import get_user_model
            Account = get_user_model()
            
            # Check for custom fields
            self.assertTrue(hasattr(Account, 'account_number'), 
                          "Account should have account_number field")
            print(f" Account model: FOUND")
            print(f" Has account_number field: YES")
            
        except Exception as e:
            self.fail(f" Account model check failed: {e}")
    
    def test_04_wallet_model_exists(self):
        """Check if Wallet model exists"""
        try:
            from transactions.models import Wallet
            
            # Check required fields
            self.assertTrue(hasattr(Wallet, 'balance'), 
                          "Wallet should have balance field")
            self.assertTrue(hasattr(Wallet, 'account'), 
                          "Wallet should have account relationship")
            
            print(f" Wallet model: FOUND")
            print(f" Has balance field: YES")
            print(f" Has account relationship: YES")
            
        except ImportError:
            print("  Wallet model: NOT FOUND (transactions app may not be installed)")
            self.skipTest("Wallet model not available")
        except Exception as e:
            self.fail(f" Wallet model check failed: {e}")
    
    def test_05_models_can_be_created(self):
        """Test if basic models can be created"""
        from django.contrib.auth import get_user_model
        Account = get_user_model()
        
        try:
            # Create a test account
            test_account = Account.objects.create(
                email="healthcheck@claverica.com",
                account_number="CLV-HC-010190-26-99"
            )
            
            print(f" Test account created: {test_account.account_number}")
            
            # Check if wallet exists
            if hasattr(test_account, 'wallet'):
                print(f" Wallet exists for account")
                print(f" Wallet balance: ${test_account.wallet.balance}")
            else:
                print("  No wallet found for account (may need to create manually)")
                
            # Clean up
            test_account.delete()
            print(" Test account cleaned up")
            
        except Exception as e:
            self.fail(f" Model creation test failed: {e}")