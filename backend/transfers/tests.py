from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from .models import Recipient, Transfer, TACCode, TransferLog
from django.utils import timezone
import uuid

# Get the actual user model class
User = get_user_model()

class RecipientModelTest(TestCase):
    def setUp(self):
        # Create user using the correct model
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='12345',
            first_name='Test',
            last_name='User'
        )
    
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
    
    def test_recipient_str_method(self):
        recipient = Recipient.objects.create(
            user=self.user,
            recipient_type='bank',
            name='Test Bank',
            country='USA'
        )
        self.assertEqual(str(recipient), "Test Bank (USA) - Bank")


class TransferModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='12345',
            first_name='Test',
            last_name='User'
        )
        
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
            currency='USD',
            fee=Decimal('5.00')
        )
        
        self.assertEqual(transfer.amount, Decimal('100.00'))
        self.assertEqual(transfer.fee, Decimal('5.00'))
        self.assertEqual(transfer.total_amount, Decimal('105.00'))
        self.assertTrue(transfer.transfer_id.startswith('TRF-'))
    
    def test_transfer_status_flow(self):
        transfer = Transfer.objects.create(
            sender=self.user,
            recipient=self.recipient,
            transfer_type='bank',
            amount=Decimal('50.00'),
            currency='USD'
        )
        
        self.assertEqual(transfer.status, 'pending')
        
        # Create log entries
        TransferLog.objects.create(
            transfer=transfer,
            status='processing',
            message='Transfer processing',
            created_by=self.user
        )
        
        self.assertEqual(transfer.logs.count(), 1)
    
    def test_transfer_str_method(self):
        transfer = Transfer.objects.create(
            sender=self.user,
            recipient=self.recipient,
            transfer_type='bank',
            amount=Decimal('100.00'),
            currency='USD'
        )
        self.assertIn('TRF-', str(transfer))
        # Also check it contains the email
        self.assertIn(self.user.email, str(transfer))
    
    def test_transfer_save_method(self):
        """Test that save method generates transfer_id and calculates total_amount"""
        transfer = Transfer(
            sender=self.user,
            recipient=self.recipient,
            transfer_type='bank',
            amount=Decimal('200.00'),
            currency='USD',
            fee=Decimal('10.00')
        )
        transfer.save()
        
        self.assertIsNotNone(transfer.transfer_id)
        self.assertTrue(transfer.transfer_id.startswith('TRF-'))
        self.assertEqual(transfer.total_amount, Decimal('210.00'))


class TACCodeModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='12345',
            first_name='Test',
            last_name='User'
        )
    
    def test_tac_code_creation(self):
        from datetime import timedelta
        
        tac = TACCode.objects.create(
            user=self.user,
            code='123456',
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        
        self.assertEqual(tac.code, '123456')
        self.assertFalse(tac.is_used)
        self.assertTrue(tac.is_valid())
        
        # Mark as used
        tac.is_used = True
        tac.used_at = timezone.now()
        tac.save()
        
        self.assertFalse(tac.is_valid())
    
    def test_tac_is_valid_method(self):
        """Test is_valid method with expired TAC"""
        tac = TACCode.objects.create(
            user=self.user,
            code='654321',
            expires_at=timezone.now() - timezone.timedelta(minutes=1)  # Expired
        )
        
        self.assertFalse(tac.is_valid())
    
    def test_tac_str_method(self):
        tac = TACCode.objects.create(
            user=self.user,
            code='123456',
            expires_at=timezone.now() + timezone.timedelta(minutes=10)
        )
        # Test matches the new format from models.py
        self.assertEqual(str(tac), f"TAC-123456 for {self.user.email}")


class TransferLogModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='12345',
            first_name='Test',
            last_name='User'
        )
            
        self.recipient = Recipient.objects.create(
            user=self.user,
            recipient_type='bank',
            name='Test Bank',
            country='USA',
            account_number='1234567890',
            account_holder='John Doe'
        )
        self.transfer = Transfer.objects.create(
            sender=self.user,
            recipient=self.recipient,
            transfer_type='bank',
            amount=Decimal('100.00'),
            currency='USD'
        )
    
    def test_transfer_log_creation(self):
        log = TransferLog.objects.create(
            transfer=self.transfer,
            status='completed',
            message='Transfer completed successfully',
            created_by=self.user
        )
        
        self.assertEqual(log.status, 'completed')
        self.assertEqual(log.transfer, self.transfer)
        self.assertIn('completed', str(log))
    
    def test_transfer_log_without_created_by(self):
        """Test creating log without created_by"""
        log = TransferLog.objects.create(
            transfer=self.transfer,
            status='processing',
            message='Processing without user'
        )
        
        self.assertEqual(log.status, 'processing')
        self.assertIsNone(log.created_by)


class TransferSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='12345',
            first_name='Test',
            last_name='User'
        )
            
        self.recipient = Recipient.objects.create(
            user=self.user,
            recipient_type='bank',
            name='Test Bank',
            country='USA',
            account_number='1234567890',
            account_holder='John Doe'
        )
    
    def test_transfer_serializer(self):
        from .serializers import TransferSerializer
        transfer = Transfer.objects.create(
            sender=self.user,
            recipient=self.recipient,
            transfer_type='bank',
            amount=Decimal('100.00'),
            currency='USD'
        )
        
        serializer = TransferSerializer(transfer)
        data = serializer.data
        
        self.assertIn('transfer_id', data)
        self.assertIn('sender_email', data)
        self.assertEqual(data['amount'], '100.00')
        self.assertEqual(data['status'], 'pending')


class RecipientSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='12345',
            first_name='Test',
            last_name='User'
        )
    
    def test_recipient_serializer(self):
        from .serializers import RecipientSerializer
        
        recipient = Recipient.objects.create(
            user=self.user,
            recipient_type='bank',
            name='Test Bank',
            country='USA',
            account_number='1234567890',
            account_holder='John Doe'
        )
        
        serializer = RecipientSerializer(recipient)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Test Bank')
        self.assertEqual(data['recipient_type'], 'bank')
        self.assertEqual(data['country'], 'USA')