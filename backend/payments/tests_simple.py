# payments/tests_simple.py
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

from django.test import TestCase
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from decimal import Decimal
from django.contrib.auth import get_user_model
from payments.models import Account, Transaction

User = get_user_model()

class SimplePaymentTests(APITestCase):
    """Simple, clean tests that should work"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test users
        self.sender = User.objects.create_user(
            email="sender@test.com",
            password="password123",
            first_name="John",
            last_name="Doe"
        )
        
        self.receiver = User.objects.create_user(
            email="receiver@test.com",
            password="password123",
            first_name="Jane",
            last_name="Smith"
        )
        
        # Create accounts - SIMPLE version
        self.sender_account = Account.objects.create(
            user=self.sender,
            account_type='checking',
            currency='USD',
            balance=Decimal('5000.00'),
            available_balance=Decimal('5000.00')
        )
        
        self.receiver_account = Account.objects.create(
            user=self.receiver,
            account_type='checking',
            currency='USD',
            balance=Decimal('2000.00'),
            available_balance=Decimal('2000.00')
        )
        
        # Authenticate
        self.client.force_authenticate(user=self.sender)
    
    def test_1_list_accounts(self):
        """Test listing accounts"""
        response = self.client.get('/api/payments/accounts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Handle paginated or non-paginated response
        if isinstance(response.data, dict) and 'results' in response.data:
            accounts = response.data['results']
        else:
            accounts = response.data
            
        self.assertGreater(len(accounts), 0)
        return True
    
    def test_2_create_transaction(self):
        """Test creating a transaction"""
        # USE CORRECT FIELD NAMES
        payload = {
            "account": self.sender_account.id,  # CORRECT: Use 'account' not 'from_account'
            "recipient_account": self.receiver_account.id,  # CORRECT: Use 'recipient_account' not 'to_account'
            "amount": "150.50",
            "currency": "USD",
            "transaction_type": "transfer",  # Required field
            "description": "Test transaction"
        }
        
        response = self.client.post('/api/payments/transactions/', payload, format='json')
        
        # Debug output
        print(f"\nCreating transaction with payload: {payload}")
        print(f"Response status: {response.status_code}")
        if response.status_code == 400:
            print(f"Validation errors: {response.data}")
        elif response.status_code == 201:
            print(f"Transaction created successfully!")
            print(f"Transaction ID: {response.data.get('transaction_id')}")
        
        self.assertIn(response.status_code, [201, 200])
        return True
    
    def test_3_get_account_balance(self):
        """Test getting account balance"""
        response = self.client.get(f'/api/payments/accounts/{self.sender_account.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # The balance is in the account detail
        if isinstance(response.data, dict):
            balance = response.data.get('balance')
            self.assertIsNotNone(balance)
        
        return True
    
    def test_4_dashboard_stats(self):
        """Test dashboard"""
        response = self.client.get('/api/payments/dashboard-stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return True

def run_simple_tests():
    """Run the simple tests"""
    print("="*60)
    print("RUNNING SIMPLE PAYMENT TESTS")
    print("="*60)
    
    test = SimplePaymentTests()
    test.setUp()
    
    tests = [
        ("List Accounts", test.test_1_list_accounts),
        ("Create Transaction", test.test_2_create_transaction),
        ("Get Account Balance", test.test_3_get_account_balance),
        ("Dashboard Stats", test.test_4_dashboard_stats),
    ]
    
    for name, method in tests:
        print(f"\nTesting: {name}")
        try:
            result = method()
            if result:
                print(f"✓ PASSED: {name}")
            else:
                print(f"✗ FAILED: {name}")
        except Exception as e:
            print(f"✗ ERROR: {name} - {e}")
    
    print("\n" + "="*60)
    print("TESTS COMPLETE")
    print("="*60)

if __name__ == '__main__':
    run_simple_tests()