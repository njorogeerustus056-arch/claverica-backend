from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
from .models import Recipient, Transfer, TACCode

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
        self.assertTrue(str(recipient).startswith('Test Bank'))
    
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
            name='Test Bank',
            country='USA',
            account_number='1234567890',
            account_holder='John Doe'
        )
    
    def test_create_transfer(self):
        transfer = Transfer.objects.create(
            sender=self.user,
            recipient=self.recipient,
            transfer_type='bank',
            amount=Decimal('100.00'),
            fee=Decimal('5.00')
        )
        self.assertEqual(transfer.total_amount, Decimal('105.00'))
        self.assertTrue(transfer.transfer_id.startswith('TRF-'))
    
    def test_transfer_requires_tac(self):
        transfer = Transfer.objects
