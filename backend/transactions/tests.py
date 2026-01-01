# transactions/tests.py
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from django.apps import apps
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

# Get models using Django's app registry to avoid import issues
Transaction = apps.get_model('transactions', 'Transaction')
TransactionLog = apps.get_model('transactions', 'TransactionLog')
User = get_user_model()  # Get the custom user model


class TransactionModelTest(TestCase):
    """Test cases for Transaction model"""
    
    def setUp(self):
        # Create a test user first
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.transaction = Transaction.objects.create(
            user_id=str(self.user.id),  # Use the actual user ID
            type='credit',
            amount=Decimal('100.00'),
            currency='USD',
            merchant='Test Merchant',
            category='income',
            transaction_date=timezone.now()
        )
    
    def test_transaction_creation(self):
        """Test that a transaction is created with auto-generated ID"""
        self.assertIsNotNone(self.transaction.transaction_id)
        self.assertTrue(self.transaction.transaction_id.startswith('FIN/'))
    
    def test_transaction_str(self):
        """Test the string representation of transaction"""
        self.assertIn(self.transaction.merchant, str(self.transaction))


class TransactionAPITest(APITestCase):
    """Test cases for Transaction API endpoints"""
    
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.user_id = str(self.user.id)  # Use the actual user ID
        
        # Create JWT token for authentication
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        
        # Configure the client with authentication
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        self.transaction_data = {
            'user_id': self.user_id,
            'type': 'credit',
            'amount': '150.00',
            'currency': 'USD',
            'merchant': 'API Test Merchant',
            'category': 'income',
            'transaction_date': timezone.now().isoformat()
        }
    
    def test_create_transaction(self):
        """Test creating a transaction via API"""
        url = reverse('create_transaction')
        response = self.client.post(url, self.transaction_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('transaction', response.data)
    
    def test_list_transactions(self):
        """Test listing transactions"""
        Transaction.objects.create(
            user_id=self.user_id,
            type='credit',
            amount=Decimal('100.00'),
            currency='USD',
            merchant='Test Merchant',
            category='income',
            transaction_date=timezone.now()
        )
        
        url = reverse('list_transactions')
        response = self.client.get(f'{url}?user_id={self.user_id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('transactions', response.data)
        self.assertIn('pagination', response.data)
    
    def test_get_stats(self):
        """Test getting transaction statistics"""
        # Create some test transactions
        Transaction.objects.create(
            user_id=self.user_id,
            type='credit',
            amount=Decimal('100.00'),
            currency='USD',
            merchant='Test 1',
            category='income',
            status='completed',
            transaction_date=timezone.now()
        )
        
        Transaction.objects.create(
            user_id=self.user_id,
            type='debit',
            amount=Decimal('50.00'),
            currency='USD',
            merchant='Test 2',
            category='shopping',
            status='completed',
            transaction_date=timezone.now()
        )
        
        url = reverse('transaction_stats')
        response = self.client.get(f'{url}?user_id={self.user_id}')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_transactions', response.data)
        self.assertIn('total_credits', response.data)
        self.assertIn('total_debits', response.data)
        self.assertIn('net_balance', response.data)
    
    def test_get_transaction_detail(self):
        """Test getting a specific transaction detail"""
        transaction = Transaction.objects.create(
            user_id=self.user_id,
            type='credit',
            amount=Decimal('200.00'),
            currency='USD',
            merchant='Detail Test',
            category='income',
            transaction_date=timezone.now()
        )
        
        url = reverse('transaction_detail', args=[transaction.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('transaction', response.data)
    
    def test_update_transaction(self):
        """Test updating a transaction"""
        transaction = Transaction.objects.create(
            user_id=self.user_id,
            type='credit',
            amount=Decimal('300.00'),
            currency='USD',
            merchant='Update Test',
            category='income',
            transaction_date=timezone.now()
        )
        
        url = reverse('update_transaction', args=[transaction.id])
        update_data = {
            'status': 'completed',
            'description': 'Updated description'
        }
        
        response = self.client.patch(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Refresh and verify
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, 'completed')
        self.assertEqual(transaction.description, 'Updated description')
    
    def test_delete_transaction(self):
        """Test soft deleting a transaction"""
        transaction = Transaction.objects.create(
            user_id=self.user_id,
            type='credit',
            amount=Decimal('400.00'),
            currency='USD',
            merchant='Delete Test',
            category='income',
            status='completed',
            transaction_date=timezone.now()
        )
        
        url = reverse('delete_transaction', args=[transaction.id])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Refresh and verify soft delete
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, 'cancelled')
    
    def test_recent_activity(self):
        """Test getting recent activity"""
        # Create multiple transactions
        for i in range(5):
            Transaction.objects.create(
                user_id=self.user_id,
                type='credit',
                amount=Decimal(f'{100 + i}.00'),
                currency='USD',
                merchant=f'Recent Test {i}',
                category='income',
                transaction_date=timezone.now()
            )
        
        url = reverse('recent_activity')
        response = self.client.get(f'{url}?user_id={self.user_id}&limit=3')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('activities', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(len(response.data['activities']), 3)
    
    def test_create_transaction_missing_user_id(self):
        """Test creating a transaction without user_id"""
        url = reverse('create_transaction')
        data = self.transaction_data.copy()
        data.pop('user_id')  # Remove user_id
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_list_transactions_missing_user_id(self):
        """Test listing transactions without user_id"""
        url = reverse('list_transactions')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_stats_missing_user_id(self):
        """Test getting stats without user_id"""
        url = reverse('transaction_stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_recent_activity_missing_user_id(self):
        """Test getting recent activity without user_id"""
        url = reverse('recent_activity')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)