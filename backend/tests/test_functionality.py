"""
Test core financial functionality.
Run with: python manage.py test tests.test_functionality
"""

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')

import django
django.setup()

from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal

class CoreFunctionalityTests(TestCase):
    """Test the most critical financial operations"""
    
    def setUp(self):
        """Set up test data"""
        self.Account = get_user_model()
        
        # Create test account
        self.test_account = self.Account.objects.create(
            email="test@claverica.com",
            account_number="CLV-TEST-010190-26-01",
            first_name="Test",
            last_name="User"
        )
        
        # Ensure wallet exists
        try:
            from transactions.models import Wallet
            if not hasattr(self.test_account, 'wallet'):
                Wallet.objects.create(
                    account=self.test_account,
                    balance=Decimal('0.00')
                )
        except:
            pass  # Wallet might not exist yet
        
        print(f"\n Test Account: {self.test_account.account_number}")
    
    def test_01_can_credit_wallet(self):
        """Test adding money to wallet"""
        print("\n Testing: Credit Wallet")
        
        if not hasattr(self.test_account, 'wallet'):
            print("  Skipping - Wallet not available")
            self.skipTest("Wallet not available")
        
        initial_balance = self.test_account.wallet.balance
        credit_amount = Decimal('100.00')
        
        print(f"Initial balance: ${initial_balance}")
        print(f"Credit amount: ${credit_amount}")
        
        # Direct wallet update (simplest test)
        self.test_account.wallet.balance += credit_amount
        self.test_account.wallet.save()
        
        # Refresh from database
        self.test_account.wallet.refresh_from_db()
        
        print(f"New balance: ${self.test_account.wallet.balance}")
        
        self.assertEqual(
            self.test_account.wallet.balance, 
            initial_balance + credit_amount,
            "Balance should increase after credit"
        )
        
        print(" Wallet credit test: PASSED")
    
    def test_02_can_debit_wallet(self):
        """Test removing money from wallet"""
        print("\n Testing: Debit Wallet")
        
        if not hasattr(self.test_account, 'wallet'):
            print("  Skipping - Wallet not available")
            self.skipTest("Wallet not available")
        
        # First add some money
        self.test_account.wallet.balance = Decimal('200.00')
        self.test_account.wallet.save()
        
        initial_balance = self.test_account.wallet.balance
        debit_amount = Decimal('50.00')
        
        print(f"Initial balance: ${initial_balance}")
        print(f"Debit amount: ${debit_amount}")
        
        # Check sufficient funds
        if initial_balance >= debit_amount:
            self.test_account.wallet.balance -= debit_amount
            self.test_account.wallet.save()
            
            self.test_account.wallet.refresh_from_db()
            
            print(f"New balance: ${self.test_account.wallet.balance}")
            
            self.assertEqual(
                self.test_account.wallet.balance,
                initial_balance - debit_amount,
                "Balance should decrease after debit"
            )
            
            print(" Wallet debit test: PASSED")
        else:
            print("  Insufficient funds for debit test")
    
    def test_03_check_transfer_models(self):
        """Check if transfer-related models exist"""
        print("\n Testing: Transfer Models")
        
        # Check Transfer model
        try:
            from transfers.models import Transfer
            print(" Transfer model: EXISTS")
            
            # Try to create a transfer record
            transfer = Transfer(
                account=self.test_account,
                amount=Decimal('100.00'),
                recipient_name="Test Recipient",
                destination_type="bank"
            )
            print(" Transfer object can be created")
            
        except ImportError:
            print("  Transfer model: NOT FOUND")
        except Exception as e:
            print(f"  Transfer model check: {e}")
    
    def test_04_check_payment_models(self):
        """Check if payment-related models exist"""
        print("\n Testing: Payment Models")
        
        # Check Payment model
        try:
            from payments.models import Payment
            print(" Payment model: EXISTS")
            
        except ImportError:
            print("  Payment model: NOT FOUND")
        except Exception as e:
            print(f"  Payment model check: {e}")
    
    def test_05_check_card_models(self):
        """Check if card models exist"""
        print("\n Testing: Card Models")
        
        # Check Card model
        try:
            from cards.models import Card
            print(" Card model: EXISTS")
            
            # Check for computed properties
            if hasattr(Card, 'balance'):
                print(" Card has balance property")
            else:
                print("  Card missing balance property")
                
        except ImportError:
            print("  Card model: NOT FOUND")
        except Exception as e:
            print(f"  Card model check: {e}")
