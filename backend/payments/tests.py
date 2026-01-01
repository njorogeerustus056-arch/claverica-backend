# payments/tests.py - FINAL CORRECTED VERSION
from django.test import TestCase
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from django.urls import reverse
from decimal import Decimal
import json

# Import models
from .models import Account, Transaction, Card
from django.contrib.auth import get_user_model

User = get_user_model()

class PaymentTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create test users
        self.user = User.objects.create_user(
            email="alice@example.com",
            password="Test1234!",
            first_name="Alice",
            last_name="Johnson"
        )
        
        # Create account for user WITH available_balance
        self.account = Account.objects.create(
            user=self.user,
            account_type='checking',
            currency='USD',
            balance=Decimal('1000.00'),
            available_balance=Decimal('1000.00')  # ADD THIS
        )
        
        # Create a second account for transfers WITH available_balance
        self.recipient_user = User.objects.create_user(
            email="bob@example.com",
            password="Test1234!",
            first_name="Bob",
            last_name="Smith"
        )
        
        self.recipient_account = Account.objects.create(
            user=self.recipient_user,
            account_type='checking',
            currency='USD',
            balance=Decimal('500.00'),
            available_balance=Decimal('500.00')  # ADD THIS
        )
        
        # Authenticate user
        self.client.force_authenticate(user=self.user)
    
    def test_create_transaction(self):
        """Test creating a payment transaction"""
        url = '/api/payments/transactions/'
        
        payload = {
            "account": self.account.id,
            "amount": "100.00",
            "transaction_type": "payment",
            "currency": "USD",
            "description": "Test payment"
        }
        
        response = self.client.post(url, payload, format='json')
        
        # Should return 201 CREATED
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check transaction was created
        self.assertEqual(Transaction.objects.count(), 1)
    
    def test_quick_transfer(self):
        """Test quick transfer between accounts"""
        url = '/api/payments/quick-transfer/'
        
        payload = {
            "recipient_account_number": self.recipient_account.account_number,
            "amount": "200.00",
            "currency": "USD",
            "description": "Test transfer"
        }
        
        response = self.client.post(url, payload, format='json')
        
        # Check if transfer was successful
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Refresh accounts
        self.account.refresh_from_db()
        self.recipient_account.refresh_from_db()
        
        # Check balances were updated
        self.assertEqual(self.account.balance, Decimal('800.00'))
        self.assertEqual(self.recipient_account.balance, Decimal('700.00'))
    
    def test_insufficient_funds(self):
        """Test transfer with insufficient funds"""
        url = '/api/payments/quick-transfer/'
        
        payload = {
            "recipient_account_number": self.recipient_account.account_number,
            "amount": "2000.00",
            "currency": "USD",
            "description": "Should fail"
        }
        
        response = self.client.post(url, payload, format='json')
        
        # Should return 400 Bad Request
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_get_account_balance(self):
        """Test getting account balance"""
        url = f'/api/payments/accounts/{self.account.id}/balance/'
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['balance'], '1000.00')
        self.assertEqual(response.data['available_balance'], '1000.00')  # ADD THIS CHECK
    
    def test_dashboard_stats(self):
        """Test dashboard statistics endpoint"""
        url = '/api/payments/dashboard-stats/'
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_balance', response.data)