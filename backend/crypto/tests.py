"""
crypto/tests.py - Test cases for crypto models and services
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from crypto.models import CryptoWallet, CryptoAsset, CryptoTransaction
from decimal import Decimal
import uuid

User = get_user_model()


class CryptoWalletTests(TestCase):
    """Test cases for CryptoWallet model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='crypto_user@example.com',
            password='testpass123',
            first_name='Crypto',
            last_name='User'
        )
        
        # Create crypto assets
        self.btc = CryptoAsset.objects.create(
            symbol='BTC',
            name='Bitcoin',
            current_price_usd=Decimal('45000.00'),
            is_active=True
        )
        
        self.eth = CryptoAsset.objects.create(
            symbol='ETH',
            name='Ethereum',
            current_price_usd=Decimal('3000.00'),
            is_active=True
        )
    
    def test_create_crypto_wallet(self):
        """Test creating a crypto wallet"""
        wallet = CryptoWallet.objects.create(
            user=self.user,
            asset=self.btc,
            wallet_address='1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa',
            balance=Decimal('1.5'),
            is_active=True
        )
        
        self.assertEqual(wallet.user, self.user)
        self.assertEqual(wallet.asset, self.btc)
        self.assertEqual(wallet.wallet_address, '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa')
        self.assertEqual(wallet.balance, Decimal('1.5'))
        self.assertTrue(wallet.is_active)
    
    def test_wallet_string_representation(self):
        """Test string representation of wallet"""
        wallet = CryptoWallet.objects.create(
            user=self.user,
            asset=self.btc,
            wallet_address='1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa',
            balance=Decimal('1.5')
        )
        
        self.assertIn('BTC', str(wallet))
        self.assertIn(str(self.user.email), str(wallet))
    
    def test_user_can_have_wallets_for_different_assets(self):
        """Test that a user can have wallets for different cryptocurrencies"""
        # Create BTC wallet
        btc_wallet = CryptoWallet.objects.create(
            user=self.user,
            asset=self.btc,
            wallet_address='btc_address_1',
            balance=Decimal('1.0')
        )
        
        # Create ETH wallet - this should work since it's a different asset
        eth_wallet = CryptoWallet.objects.create(
            user=self.user,
            asset=self.eth,
            wallet_address='eth_address_1',
            balance=Decimal('10.0')
        )
        
        wallets = CryptoWallet.objects.filter(user=self.user)
        self.assertEqual(wallets.count(), 2)
        
        # Check that we have both BTC and ETH wallets
        self.assertEqual(wallets[0].asset.symbol, 'BTC')
        self.assertEqual(wallets[1].asset.symbol, 'ETH')


class CryptoAssetTests(TestCase):
    """Test cases for CryptoAsset model"""
    
    def test_create_crypto_asset(self):
        """Test creating a cryptocurrency"""
        crypto = CryptoAsset.objects.create(
            symbol='ETH',
            name='Ethereum',
            current_price_usd=Decimal('3000.00'),
            is_active=True
        )
        
        self.assertEqual(crypto.symbol, 'ETH')
        self.assertEqual(crypto.name, 'Ethereum')
        self.assertEqual(crypto.current_price_usd, Decimal('3000.00'))
        self.assertTrue(crypto.is_active)
    
    def test_cryptocurrency_string_representation(self):
        """Test string representation of cryptocurrency"""
        crypto = CryptoAsset.objects.create(
            symbol='ETH',
            name='Ethereum',
            current_price_usd=Decimal('3000.00')
        )
        
        self.assertEqual(str(crypto), 'ETH - Ethereum')


class CryptoTransactionTests(TestCase):
    """Test cases for CryptoTransaction model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='transaction_user@example.com',
            password='testpass123',
            first_name='Transaction',
            last_name='User'
        )
        
        # Create crypto assets
        self.btc = CryptoAsset.objects.create(
            symbol='BTC',
            name='Bitcoin',
            current_price_usd=Decimal('45000.00'),
            is_active=True
        )
        
        self.eth = CryptoAsset.objects.create(
            symbol='ETH',
            name='Ethereum',
            current_price_usd=Decimal('3000.00'),
            is_active=True
        )
        
        # Create wallets - DIFFERENT assets to avoid unique constraint
        self.sender_wallet = CryptoWallet.objects.create(
            user=self.user,
            asset=self.btc,
            wallet_address='sender_btc_address',
            balance=Decimal('5.0')
        )
        
        self.receiver_wallet = CryptoWallet.objects.create(
            user=self.user,
            asset=self.eth,  # Different asset to avoid unique constraint
            wallet_address='receiver_eth_address',
            balance=Decimal('0.0')
        )
    
    def test_create_transaction(self):
        """Test creating a transaction"""
        # Create a swap transaction (BTC to ETH)
        transaction = CryptoTransaction.objects.create(
            user=self.user,
            asset=self.btc,
            from_wallet=self.sender_wallet,
            to_wallet=self.receiver_wallet,
            amount=Decimal('1.0'),
            fee=Decimal('0.001'),
            transaction_type='swap',  # Changed to swap since different assets
            status='pending',
            swap_to_asset=self.eth,  # Specify what we're swapping to
            swap_rate=Decimal('15.0')  # 1 BTC = 15 ETH
        )
        
        self.assertEqual(transaction.user, self.user)
        self.assertEqual(transaction.asset, self.btc)
        self.assertEqual(transaction.from_wallet, self.sender_wallet)
        self.assertEqual(transaction.to_wallet, self.receiver_wallet)
        self.assertEqual(transaction.amount, Decimal('1.0'))
        self.assertEqual(transaction.fee, Decimal('0.001'))
        self.assertEqual(transaction.transaction_type, 'swap')
        self.assertEqual(transaction.status, 'pending')
        self.assertEqual(transaction.swap_to_asset, self.eth)
        self.assertEqual(transaction.swap_rate, Decimal('15.0'))
    
    def test_transaction_string_representation(self):
        """Test string representation of transaction"""
        transaction = CryptoTransaction.objects.create(
            user=self.user,
            asset=self.btc,
            from_wallet=self.sender_wallet,
            to_wallet=self.receiver_wallet,
            amount=Decimal('1.0'),
            fee=Decimal('0.001'),
            transaction_type='swap',
            status='pending'
        )
        
        # Check the actual string format from your model's __str__ method
        expected_str = f"{self.user.email} - swap - {Decimal('1.0')} BTC"
        self.assertEqual(str(transaction), expected_str)


class CryptoIntegrationTests(TestCase):
    """Integration tests for crypto functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='integration@example.com',
            password='testpass123',
            first_name='Integration',
            last_name='Test'
        )
        
        self.btc = CryptoAsset.objects.create(
            symbol='BTC',
            name='Bitcoin',
            current_price_usd=Decimal('45000.00'),
            is_active=True
        )
        
        self.eth = CryptoAsset.objects.create(
            symbol='ETH',
            name='Ethereum',
            current_price_usd=Decimal('3000.00'),
            is_active=True
        )
    
    def test_user_can_have_multiple_wallets_for_different_assets(self):
        """Test that a user can have multiple crypto wallets for different assets"""
        wallet1 = CryptoWallet.objects.create(
            user=self.user,
            asset=self.btc,
            wallet_address='btc_address_1',
            balance=Decimal('1.0')
        )
        
        wallet2 = CryptoWallet.objects.create(
            user=self.user,
            asset=self.eth,  # Different asset
            wallet_address='eth_address_1',
            balance=Decimal('2.0')
        )
        
        wallets = CryptoWallet.objects.filter(user=self.user)
        self.assertEqual(wallets.count(), 2)
        
        # Verify we have both BTC and ETH
        assets = [wallet.asset.symbol for wallet in wallets]
        self.assertIn('BTC', assets)
        self.assertIn('ETH', assets)
    
    def test_transaction_workflow(self):
        """Test complete transaction workflow"""
        # Create two different users for sender/receiver (with required fields)
        sender = User.objects.create_user(
            email='sender@example.com',
            password='testpass123',
            first_name='Sender',
            last_name='User'
        )
        
        receiver = User.objects.create_user(
            email='receiver@example.com',
            password='testpass123',
            first_name='Receiver',
            last_name='User'
        )
        
        # Create wallets for sender
        sender_wallet = CryptoWallet.objects.create(
            user=sender,
            asset=self.btc,
            wallet_address='sender_address',
            balance=Decimal('5.0')
        )
        
        # Create wallets for receiver
        receiver_wallet = CryptoWallet.objects.create(
            user=receiver,
            asset=self.btc,
            wallet_address='receiver_address',
            balance=Decimal('0.0')
        )
        
        # Create a send transaction
        transaction = CryptoTransaction.objects.create(
            user=sender,  # Sender initiates the transaction
            asset=self.btc,
            from_wallet=sender_wallet,
            to_wallet=receiver_wallet,
            amount=Decimal('1.0'),
            fee=Decimal('0.001'),
            transaction_type='send',
            status='pending'
        )
        
        # Verify transaction was created
        self.assertEqual(transaction.status, 'pending')
        self.assertEqual(transaction.amount, Decimal('1.0'))
        self.assertEqual(transaction.from_wallet, sender_wallet)
        self.assertEqual(transaction.to_wallet, receiver_wallet)
        
        # Simulate transaction completion
        transaction.status = 'completed'
        transaction.save()
        
        self.assertEqual(transaction.status, 'completed')