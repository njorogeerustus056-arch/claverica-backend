# test_payments_comprehensive.py - FIXED VERSION
import os
import django
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.test import TestCase
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from decimal import Decimal
from django.contrib.auth import get_user_model

User = get_user_model()

print("="*60)
print("FIXED PAYMENT TESTS - Using correct User model")
print("="*60)

class FixedPaymentTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create test users WITHOUT username field
        self.sender = User.objects.create_user(
            email="sender@example.com",
            password="password123",
            first_name="Sender",
            last_name="User"
        )
        
        self.receiver = User.objects.create_user(
            email="receiver@example.com",
            password="password123",
            first_name="Receiver",
            last_name="User"
        )
        
        print(f"✓ Created sender: {self.sender.email}")
        print(f"✓ Created receiver: {self.receiver.email}")
        
        # Create accounts
        from payments.models import Account
        
        self.sender_account = Account.objects.create(
            user=self.sender,
            account_type='checking',
            currency='USD',
            balance=Decimal('5000.00'),
            available_balance=Decimal('5000.00')
        )
        
        self.receiver_account = Account.objects.create(
            user=self.receiver,
            account_type='savings',
            currency='USD',
            balance=Decimal('2000.00'),
            available_balance=Decimal('2000.00')
        )
        
        print(f"✓ Created sender account: {self.sender_account.account_number}")
        print(f"✓ Created receiver account: {self.receiver_account.account_number}")
        
        # Authenticate as sender
        self.client.force_authenticate(user=self.sender)
    
    def get_response_data(self, response):
        """Helper to handle both paginated and non-paginated responses"""
        if response.status_code not in [200, 201]:
            return []
        
        data = response.data
        if isinstance(data, dict) and 'results' in data:
            return data['results']  # Paginated response
        elif isinstance(data, list):
            return data  # List response
        elif isinstance(data, dict):
            return [data]  # Single object
        return []
    
    def test_1_account_list(self):
        """Test listing user's accounts"""
        print("\n=== Test 1: List Accounts ===")
        response = self.client.get('/api/payments/accounts/')
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            accounts = self.get_response_data(response)
            print(f"Accounts: {len(accounts)} account(s)")
            
            for account in accounts:
                if isinstance(account, dict):
                    print(f"  - {account.get('account_number')}: ${account.get('balance')}")
                else:
                    print(f"  - Account object: {account}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return True
    
    def test_2_create_transaction(self):
        """Test creating a payment transaction"""
        print("\n=== Test 2: Create Transaction ===")
        
        payload = {
            "account": self.sender_account.id,
            "amount": "150.50",
            "transaction_type": "payment",
            "currency": "USD",
            "description": "Test payment to merchant"
        }
        
        response = self.client.post('/api/payments/transactions/', payload, format='json')
        
        print(f"Status: {response.status_code}")
        if response.status_code == 201:
            data = response.data
            if isinstance(data, dict):
                print(f"✓ Transaction created: {data.get('transaction_id')}")
                print(f"  Amount: ${data.get('amount')}")
                print(f"  Status: {data.get('status')}")
        else:
            print(f"✗ Error: {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return True
    
    def test_3_quick_transfer(self):
        """Test transferring funds between accounts"""
        print("\n=== Test 3: Quick Transfer ===")
        
        print(f"Before transfer:")
        print(f"  Sender balance: ${self.sender_account.balance}")
        print(f"  Receiver balance: ${self.receiver_account.balance}")
        
        payload = {
            "recipient_account_number": self.receiver_account.account_number,
            "amount": "750.25",
            "currency": "USD",
            "description": "Family support"
        }
        
        response = self.client.post('/api/payments/quick-transfer/', payload, format='json')
        
        print(f"\nTransfer Status: {response.status_code}")
        
        if response.status_code == 201:
            # Refresh accounts
            self.sender_account.refresh_from_db()
            self.receiver_account.refresh_from_db()
            
            print(f"✓ Transfer successful!")
            print(f"After transfer:")
            print(f"  Sender balance: ${self.sender_account.balance}")
            print(f"  Receiver balance: ${self.receiver_account.balance}")
            
            from payments.models import Transaction
            tx_count = Transaction.objects.count()
            print(f"  Total transactions: {tx_count}")
        else:
            print(f"✗ Error: {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return True
    
    def test_4_dashboard_stats(self):
        """Test dashboard statistics"""
        print("\n=== Test 4: Dashboard Stats ===")
        
        response = self.client.get('/api/payments/dashboard-stats/')
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            stats = response.data
            if isinstance(stats, dict):
                print(f"✓ Dashboard stats retrieved:")
                print(f"  Total Balance: ${stats.get('total_balance', 0)}")
                print(f"  Currency: {stats.get('currency', 'N/A')}")
                print(f"  Active Cards: {stats.get('active_cards', 0)}")
                print(f"  Pending Transactions: {stats.get('pending_transactions', 0)}")
        else:
            print(f"✗ Error: {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return True
    
    def test_5_get_account_balance(self):
        """Test getting specific account balance"""
        print("\n=== Test 5: Account Balance ===")
        
        url = f'/api/payments/accounts/{self.sender_account.id}/balance/'
        response = self.client.get(url)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            balance = response.data
            if isinstance(balance, dict):
                print(f"✓ Account balance:")
                print(f"  Balance: ${balance.get('balance', 0)}")
                print(f"  Available: ${balance.get('available_balance', 0)}")
                print(f"  Currency: {balance.get('currency', 'N/A')}")
        else:
            print(f"✗ Error: {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return True

def run_tests():
    print("\n" + "="*60)
    print("RUNNING PAYMENT TESTS")
    print("="*60)
    
    test = FixedPaymentTests()
    
    # Run setup
    print("Setting up test data...")
    test.setUp()
    
    # Run each test
    tests = [
        ("List Accounts", test.test_1_account_list),
        ("Create Transaction", test.test_2_create_transaction),
        ("Quick Transfer", test.test_3_quick_transfer),
        ("Dashboard Stats", test.test_4_dashboard_stats),
        ("Account Balance", test.test_5_get_account_balance),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_method in tests:
        print(f"\n{'='*40}")
        print(f"TEST: {test_name}")
        print('='*40)
        
        try:
            result = test_method()
            if result:
                print(f"✓ PASSED: {test_name}")
                passed += 1
            else:
                print(f"✗ FAILED: {test_name}")
                failed += 1
        except AssertionError as e:
            print(f"✗ ASSERTION FAILED: {test_name}")
            print(f"  Error: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ ERROR: {test_name}")
            print(f"  Exception: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*60)
    
    return passed, failed

if __name__ == '__main__':
    run_tests()