from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Transaction, TransactionLog
from datetime import datetime
from decimal import Decimal


class TransactionModelTest(TestCase):
    def setUp(self):
        self.transaction = Transaction.objects.create(
            user_id='test_user',
            type='credit',
            amount=Decimal('100.00'),
            currency='USD',
            merchant='Test Merchant',
            category='income',
            transaction_date=datetime.now()
        )
    
    def test_transaction_creation(self):
        """Test that a transaction is created with auto-generated ID"""
        self.assertIsNotNone(self.transaction.transaction_id)
        self.assertTrue(self.transaction.transaction_id.startswith('FIN/'))
    
    def test_transaction_str(self):
        """Test the string representation of transaction"""
        self.assertIn(self.transaction.merchant, str(self.transaction))


class TransactionAPITest(APITestCase):
    def setUp(self):
        self.user_id = 'test_user'
        self.transaction_data = {
            'user_id': self.user_id,
            'type': 'credit',
            'amount': '150.00',
            'currency': 'USD',
            'merchant': 'API Test Merchant',
            'category': 'income',
            'transaction_date': datetime.now().isoformat()
        }
    
    def test_create_transaction(self):
        """Test creating a transaction via API"""
        response = self.client.post('/api/transactions/create/', self.transaction_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('transaction', response.data)
    
    def test_list_transactions(self):
        """Test listing transactions"""
        Transaction.objects.create(
            user_id=self.user_id,
            type='credit',
            amount=Decimal('100.00'),
            merchant='Test',
            transaction_date=datetime.now()
        )
        response = self.client.get(f'/api/transactions/list/?user_id={self.user_id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('transactions', response.data)
    
    def test_get_stats(self):
        """Test getting transaction statistics"""
        response = self.client.get(f'/api/transactions/stats/?user_id={self.user_id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_transactions', response.data)
