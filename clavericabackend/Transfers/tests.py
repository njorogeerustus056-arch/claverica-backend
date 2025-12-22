from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
from .models import Recipient, Transfer, TACCode, TransferLog

class RecipientModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
    
    def test_create_bank_recipient(self):
        recipient = Recipient.objects.create(
            user=self.user,
            recipient_type='bank',
            name='Test Bank',
            country='USA',
            account_number='1234567890',
            account_holder='John Doe'
        )
        self.assertEqual(recipient.recipient_type, 'bank')
        self.assertIn('Test Bank', str(recipient))
    
    def test_create_crypto_recipient(self):
        recipient = Recipient.objects.create(
            user=self.user,
            recipient_type='crypto',
            name='Bitcoin Wallet',
            country='Global',
            wallet_address='1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa',
            network='BTC'
        )
        self.assertEqual(recipient.recipient_type, 'crypto')
        self.assertIsNotNone(recipient.wallet_address)


class TransferModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.recipient = Recipient.objects.create(
            user=self.user,
            recipient_type='bank',
            name='Test
