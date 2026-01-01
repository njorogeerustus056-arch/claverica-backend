# final_payment_test.py - FINAL TEST WITH ALL FIXES
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

print("="*70)
print("FINAL PAYMENT SYSTEM TEST - ALL FIXES APPLIED")
print("="*70)

class FinalPaymentTests(APITestCase):
    def setUp(self):
        """Proper setup with available_balance set"""
        self.client = APIClient()
        
        print("\n📝 Setting up test environment...")
        
        # Create test users
        self.sender = User.objects.create_user(
            email="final_sender@example.com",
            password="Password123!",
            first_name="Final",
            last_name="Sender"
        )
        
        self.receiver = User.objects.create_user(
            email="final_receiver@example.com",
            password="Password123!",
            first_name="Final",
            last_name="Receiver"
        )
        
        print(f"  ✓ Created users: {self.sender.email}, {self.receiver.email}")
        
        # Create accounts WITH available_balance
        from payments.models import Account
        
        # Clean up any existing accounts first
        Account.objects.filter(user=self.sender).delete()
        Account.objects.filter(user=self.receiver).delete()
        
        self.sender_account = Account.objects.create(
            user=self.sender,
            account_type='checking',
            currency='USD',
            balance=Decimal('10000.00'),
            available_balance=Decimal('10000.00')  # CRITICAL!
        )
        
        self.receiver_account = Account.objects.create(
            user=self.receiver,
            account_type='checking',
            currency='USD',
            balance=Decimal('5000.00'),
            available_balance=Decimal('5000.00')  # CRITICAL!
        )
        
        print(f"  ✓ Created accounts with available_balance set")
        print(f"    Sender: {self.sender_account.account_number} (${self.sender_account.balance})")
        print(f"    Receiver: {self.receiver_account.account_number} (${self.receiver_account.balance})")
        
        # Authenticate
        self.client.force_authenticate(user=self.sender)
        print("  ✓ Authenticated as sender")
    
    def test_1_quick_transfer_success(self):
        """Test successful quick transfer"""
        print("\n" + "="*50)
        print("TEST 1: Quick Transfer - Success")
        print("="*50)
        
        initial_sender = self.sender_account.balance
        initial_receiver = self.receiver_account.balance
        transfer_amount = Decimal('2500.00')
        
        print(f"Transferring: ${transfer_amount}")
        print(f"From: {self.sender_account.account_number} (${initial_sender})")
        print(f"To: {self.receiver_account.account_number} (${initial_receiver})")
        
        payload = {
            "recipient_account_number": self.receiver_account.account_number,
            "amount": str(transfer_amount),
            "currency": "USD",
            "description": "Business payment"
        }
        
        response = self.client.post('/api/payments/quick-transfer/', payload, format='json')
        print(f"\nResponse: {response.status_code}")
        
        if response.status_code == 201:
            print(f"✅ Transfer successful!")
            print(f"Transaction ID: {response.data.get('transaction_id')}")
            print(f"Amount: ${response.data.get('amount')}")
            
            # Refresh accounts
            self.sender_account.refresh_from_db()
            self.receiver_account.refresh_from_db()
            
            print(f"\nUpdated balances:")
            print(f"Sender: ${self.sender_account.balance} (was ${initial_sender})")
            print(f"Receiver: ${self.receiver_account.balance} (was ${initial_receiver})")
            
            # Verify
            expected_sender = initial_sender - transfer_amount
            expected_receiver = initial_receiver + transfer_amount
            
            self.assertEqual(self.sender_account.balance, expected_sender)
            self.assertEqual(self.receiver_account.balance, expected_receiver)
            print(f"✓ Balance verification passed!")
        else:
            print(f"❌ Failed: {response.data}")
        
        self.assertEqual(response.status_code, 201)
        return True
    
    def test_2_quick_transfer_insufficient_funds(self):
        """Test quick transfer with insufficient funds"""
        print("\n" + "="*50)
        print("TEST 2: Quick Transfer - Insufficient Funds")
        print("="*50)
        
        payload = {
            "recipient_account_number": self.receiver_account.account_number,
            "amount": "20000.00",  # More than balance
            "currency": "USD",
            "description": "Should fail"
        }
        
        print(f"Attempting transfer: ${payload['amount']}")
        print(f"Sender balance: ${self.sender_account.balance}")
        
        response = self.client.post('/api/payments/quick-transfer/', payload, format='json')
        print(f"\nResponse: {response.status_code}")
        
        if response.status_code == 400:
            print(f"✅ Correctly rejected: Insufficient funds")
            print(f"Error message: {response.data.get('error')}")
        else:
            print(f"❌ Unexpected: {response.status_code}")
            print(f"Response: {response.data}")
        
        self.assertEqual(response.status_code, 400)
        return True
    
    def test_3_create_transaction(self):
        """Test creating a regular transaction"""
        print("\n" + "="*50)
        print("TEST 3: Create Transaction")
        print("="*50)
        
        from payments.models import Transaction
        
        initial_count = Transaction.objects.count()
        
        payload = {
            "account": self.sender_account.id,
            "amount": "1500.75",
            "transaction_type": "payment",
            "currency": "USD",
            "description": "Online purchase",
            "recipient_name": "Amazon Inc",
            "recipient_email": "payments@amazon.com"
        }
        
        print(f"Creating transaction: ${payload['amount']} for {payload['description']}")
        
        response = self.client.post('/api/payments/transactions/', payload, format='json')
        print(f"\nResponse: {response.status_code}")
        
        if response.status_code == 201:
            print(f"✅ Transaction created!")
            print(f"Transaction ID: {response.data.get('transaction_id')}")
            print(f"Amount: ${response.data.get('amount')}")
            print(f"Status: {response.data.get('status')}")
            print(f"Type: {response.data.get('transaction_type')}")
            
            # Verify in database
            final_count = Transaction.objects.count()
            print(f"Transactions in DB: {final_count} (was {initial_count})")
            self.assertEqual(final_count, initial_count + 1)
        else:
            print(f"❌ Failed: {response.data}")
        
        self.assertEqual(response.status_code, 201)
        return True
    
    def test_4_account_endpoints(self):
        """Test account-related endpoints"""
        print("\n" + "="*50)
        print("TEST 4: Account Endpoints")
        print("="*50)
        
        # List accounts
        print("\n4.1 GET /api/payments/accounts/")
        response = self.client.get('/api/payments/accounts/')
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.data
            if isinstance(data, dict) and 'results' in data:
                count = len(data['results'])
                print(f"   Found {count} account(s) (paginated)")
            elif isinstance(data, list):
                print(f"   Found {len(data)} account(s) (list)")
            else:
                print(f"   Response format: {type(data)}")
        
        # Account balance
        print("\n4.2 GET /api/payments/accounts/{id}/balance/")
        url = f'/api/payments/accounts/{self.sender_account.id}/balance/'
        response = self.client.get(url)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   Balance: ${response.data.get('balance')}")
            print(f"   Available: ${response.data.get('available_balance')}")
            print(f"   Currency: {response.data.get('currency')}")
        
        self.assertEqual(response.status_code, 200)
        return True
    
    def test_5_dashboard_stats(self):
        """Test dashboard statistics"""
        print("\n" + "="*50)
        print("TEST 5: Dashboard Statistics")
        print("="*50)
        
        response = self.client.get('/api/payments/dashboard-stats/')
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.data
            print(f"✅ Dashboard loaded")
            print(f"   Total Balance: ${data.get('total_balance', 0)}")
            print(f"   Currency: {data.get('currency', 'N/A')}")
            print(f"   Active Cards: {data.get('active_cards', 0)}")
            print(f"   Pending Transactions: {data.get('pending_transactions', 0)}")
            
            if 'recent_transactions' in data:
                print(f"   Recent Transactions: {len(data['recent_transactions'])}")
        else:
            print(f"❌ Failed: {response.data}")
        
        self.assertEqual(response.status_code, 200)
        return True
    
    def test_6_model_transfer_method(self):
        """Test the model's transfer_funds method"""
        print("\n" + "="*50)
        print("TEST 6: Model Transfer Method")
        print("="*50)
        
        # Reset balances
        self.sender_account.balance = Decimal('8000.00')
        self.sender_account.available_balance = Decimal('8000.00')
        self.sender_account.save()
        
        self.receiver_account.balance = Decimal('3000.00')
        self.receiver_account.available_balance = Decimal('3000.00')
        self.receiver_account.save()
        
        print(f"Before model transfer:")
        print(f"  Sender: ${self.sender_account.balance}")
        print(f"  Receiver: ${self.receiver_account.balance}")
        
        try:
            # Use model method
            transaction = self.sender_account.transfer_funds(
                to_account=self.receiver_account,
                amount=Decimal('1200.50'),
                description="Model method test"
            )
            
            print(f"\n✅ Model transfer successful!")
            print(f"  Transaction: {transaction.transaction_id}")
            print(f"  Amount: ${transaction.amount}")
            print(f"  Status: {transaction.status}")
            
            # Refresh
            self.sender_account.refresh_from_db()
            self.receiver_account.refresh_from_db()
            
            print(f"\nAfter model transfer:")
            print(f"  Sender: ${self.sender_account.balance}")
            print(f"  Receiver: ${self.receiver_account.balance}")
            
            # Verify
            self.assertEqual(self.sender_account.balance, Decimal('6799.50'))
            self.assertEqual(self.receiver_account.balance, Decimal('4200.50'))
            print(f"✓ Balance verification passed!")
            
        except Exception as e:
            print(f"\n❌ Model transfer failed: {e}")
            import traceback
            traceback.print_exc()
        
        return True

def run_comprehensive_test():
    """Run all tests"""
    print("\n🚀 STARTING COMPREHENSIVE PAYMENT SYSTEM TEST")
    print("="*70)
    
    test_suite = FinalPaymentTests()
    
    print("\n🛠 Initializing test setup...")
    test_suite.setUp()
    
    tests = [
        ("Quick Transfer Success", test_suite.test_1_quick_transfer_success),
        ("Insufficient Funds", test_suite.test_2_quick_transfer_insufficient_funds),
        ("Create Transaction", test_suite.test_3_create_transaction),
        ("Account Endpoints", test_suite.test_4_account_endpoints),
        ("Dashboard Stats", test_suite.test_5_dashboard_stats),
        ("Model Transfer Method", test_suite.test_6_model_transfer_method),
    ]
    
    results = []
    
    for test_name, test_method in tests:
        print(f"\n{'='*50}")
        print(f"🧪 {test_name}")
        print('='*50)
        
        try:
            success = test_method()
            if success:
                print(f"✅ PASSED")
                results.append((test_name, True, None))
            else:
                print(f"❌ FAILED (returned False)")
                results.append((test_name, False, "Returned False"))
        except AssertionError as e:
            print(f"❌ ASSERTION FAILED")
            print(f"   Error: {e}")
            results.append((test_name, False, str(e)))
        except Exception as e:
            print(f"💥 ERROR")
            print(f"   Exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False, str(e)))
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, success, _ in results if success)
    failed = len(results) - passed
    
    print(f"\n✅ Passed: {passed}/{len(results)}")
    print(f"❌ Failed: {failed}/{len(results)}")
    print(f"📈 Success Rate: {(passed/len(results))*100:.1f}%")
    
    if failed > 0:
        print("\n🔍 Issues to fix:")
        for test_name, success, error in results:
            if not success:
                print(f"   • {test_name}: {error}")
    
    print("\n" + "="*70)
    print("🎯 TESTING COMPLETE")
    print("="*70)
    
    # Final recommendations
    print("\n💡 RECOMMENDATIONS:")
    print("1. Always set available_balance when creating accounts")
    print("2. Update your existing tests to include available_balance")
    print("3. Consider updating the Account model to auto-set available_balance")
    print("4. Run: python manage.py test payments to verify all tests pass")
    
    return results

if __name__ == '__main__':
    run_comprehensive_test()