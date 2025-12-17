"""
Tests for Cards app
"""

from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
from .models import Card, Transaction, CardType, CardStatus


class CardModelTest(TestCase):
    """Test cases for Card model"""
    
    def setUp(self):
        """Set up test user and card"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.card = Card.objects.create(
            user=self.user,
            card_type=CardType.VIRTUAL,
            card_number='1234567890123456',
            last_four='3456',
            cvv='123',
            expiry_date='12/28',
            cardholder_name='Test User',
            balance=Decimal('100.00'),
            spending_limit=Decimal('5000.00')
        )
    
    def test_card_creation(self):
        """Test card is created correctly"""
        self.assertEqual(self.card.user, self.user)
        self.assertEqual(self.card.card_type, CardType.VIRTUAL)
        self.assertEqual(self.card.balance, Decimal('100.00'))
        self.assertEqual(self.card.status, CardStatus.ACTIVE)
    
    def test_masked_number(self):
        """Test masked card number property"""
        self.assertEqual(self.card.masked_number, '**** **** **** 3456')
    
    def test_card_string_representation(self):
        """Test card string representation"""
        self.assertIn('Virtual Card', str(self.card))
        self.assertIn('3456', str(self.card))


class TransactionModelTest(TestCase):
    """Test cases for Transaction model"""
    
    def setUp(self):
        """Set up test user, card, and transaction"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.card = Card.objects.create(
            user=self.user,
            card_type=CardType.VIRTUAL,
            card_number='1234567890123456',
            last_four='3456',
            cvv='123',
            expiry_date='12/28',
            cardholder_name='Test User'
        )
        
        self.transaction = Transaction.objects.create(
            user=self.user,
            card=self.card,
            amount=Decimal('50.00'),
            merchant='Test Merchant',
            category='shopping',
            transaction_type='debit',
            status='completed'
        )
    
    def test_transaction_creation(self):
        """Test transaction is created correctly"""
        self.assertEqual(self.transaction.user, self.user)
        self.assertEqual(self.transaction.card, self.card)
        self.assertEqual(self.transaction.amount, Decimal('50.00'))
        self.assertEqual(self.transaction.transaction_type, 'debit')
        self.assertEqual(self.transaction.status, 'completed')
    
    def test_transaction_string_representation(self):
        """Test transaction string representation"""
        self.assertIn('Debit', str(self.transaction))
        self.assertIn('50', str(self.transaction))
        self.assertIn('Test Merchant', str(self.transaction))
