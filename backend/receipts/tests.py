"""
receipts/tests.py - FIXED FOR ACTUAL MODEL
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from receipts.models import Receipt
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
import uuid

User = get_user_model()


class ReceiptModelTests(TestCase):
    """Test cases for Receipt model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create a sample file
        self.test_file = SimpleUploadedFile(
            "test_receipt.txt",
            b"Sample receipt content",
            content_type="text/plain"
        )
    
    def test_create_receipt(self):
        """Test creating a receipt with required fields"""
        receipt = Receipt.objects.create(
            user=self.user,
            file=self.test_file,
            merchant_name="Test Store",
            amount=10.50,
            currency="USD",
            category="other",
            original_file_name="test_receipt.txt",
            file_size=len(b"Sample receipt content"),
            file_type="text/plain"
        )
        
        self.assertEqual(receipt.user, self.user)
        self.assertEqual(receipt.merchant_name, "Test Store")
        self.assertEqual(receipt.amount, 10.50)
        self.assertEqual(receipt.currency, "USD")
        self.assertEqual(receipt.category, "other")
        self.assertEqual(receipt.status, 'pending')
    
    def test_receipt_string_representation(self):
        """Test string representation of receipt"""
        receipt = Receipt.objects.create(
            user=self.user,
            file=self.test_file,
            merchant_name="Test Store",
            amount=10.50,
            currency="USD",
            original_file_name="test_receipt.txt",
            file_size=len(b"Sample receipt content"),
            file_type="text/plain"
        )
        
        # Check string representation
        self.assertIn(self.user.email, str(receipt))
        self.assertIn("test_receipt.txt", str(receipt))
    
    def test_receipt_file_properties(self):
        """Test receipt file properties"""
        receipt = Receipt.objects.create(
            user=self.user,
            file=self.test_file,
            merchant_name="Test Store",
            amount=10.50,
            currency="USD",
            original_file_name="test_receipt.txt",
            file_size=len(b"Sample receipt content"),
            file_type="text/plain"
        )
        
        # Check file properties
        self.assertIsNotNone(receipt.file)
        self.assertEqual(receipt.original_file_name, "test_receipt.txt")
        self.assertEqual(receipt.file_size, len(b"Sample receipt content"))
        self.assertEqual(receipt.file_type, "text/plain")
    
    def test_receipt_default_status(self):
        """Test default status values for receipt"""
        receipt = Receipt.objects.create(
            user=self.user,
            file=self.test_file,
            merchant_name="Test Store",
            amount=10.50,
            currency="USD",
            original_file_name="test_receipt.txt",
            file_size=len(b"Sample receipt content"),
            file_type="text/plain"
        )
        
        self.assertEqual(receipt.status, 'pending')
    
    def test_receipt_with_optional_fields(self):
        """Test creating receipt with optional fields"""
        receipt = Receipt.objects.create(
            user=self.user,
            file=self.test_file,
            merchant_name="Test Store",
            amount=10.50,
            currency="USD",
            original_file_name="test_receipt.txt",
            file_size=len(b"Sample receipt content"),
            file_type="text/plain",
            category="food",
            transaction_date=timezone.now(),
            notes="Business expense",
            tags=["business", "lunch"]
        )
        
        self.assertEqual(receipt.category, "food")
        self.assertIsNotNone(receipt.transaction_date)
        self.assertEqual(receipt.notes, "Business expense")
        self.assertEqual(receipt.tags, ["business", "lunch"])
    
    def test_receipt_user_relationship(self):
        """Test receipt belongs to user"""
        receipt = Receipt.objects.create(
            user=self.user,
            file=self.test_file,
            merchant_name="Test Store",
            amount=10.50,
            currency="USD",
            original_file_name="test_receipt.txt",
            file_size=len(b"Sample receipt content"),
            file_type="text/plain"
        )
        
        # Test forward relationship
        self.assertEqual(receipt.user, self.user)
        
        # Test backward relationship
        user_receipts = self.user.receipts.all()
        self.assertIn(receipt, user_receipts)
    
    def test_receipt_decimal_amount(self):
        """Test receipt amount as decimal"""
        receipt = Receipt.objects.create(
            user=self.user,
            file=self.test_file,
            merchant_name="Test Store",
            amount=19.99,
            currency="USD",
            original_file_name="test_receipt.txt",
            file_size=len(b"Sample receipt content"),
            file_type="text/plain"
        )
        
        # Amount should be stored as decimal
        self.assertEqual(float(receipt.amount), 19.99)
    
    def test_receipt_currency_choices(self):
        """Test receipt currency choices"""
        receipt = Receipt.objects.create(
            user=self.user,
            file=self.test_file,
            merchant_name="Test Store",
            amount=10.50,
            currency="EUR",  # Non-default currency
            original_file_name="test_receipt.txt",
            file_size=len(b"Sample receipt content"),
            file_type="text/plain"
        )
        
        self.assertEqual(receipt.currency, "EUR")
    
    def test_receipt_category_choices(self):
        """Test receipt category choices"""
        receipt = Receipt.objects.create(
            user=self.user,
            file=self.test_file,
            merchant_name="Test Store",
            amount=10.50,
            currency="USD",
            original_file_name="test_receipt.txt",
            file_size=len(b"Sample receipt content"),
            file_type="text/plain",
            category="travel"
        )
        
        self.assertEqual(receipt.category, "travel")
    
    def test_receipt_auto_timestamps(self):
        """Test receipt uploaded_at and updated_at timestamps"""
        receipt = Receipt.objects.create(
            user=self.user,
            file=self.test_file,
            merchant_name="Test Store",
            amount=10.50,
            currency="USD",
            original_file_name="test_receipt.txt",
            file_size=len(b"Sample receipt content"),
            file_type="text/plain"
        )
        
        self.assertIsNotNone(receipt.uploaded_at)
        self.assertIsNotNone(receipt.updated_at)
    
    def test_receipt_status_changes(self):
        """Test receipt status changes"""
        receipt = Receipt.objects.create(
            user=self.user,
            file=self.test_file,
            merchant_name="Test Store",
            amount=10.50,
            currency="USD",
            original_file_name="test_receipt.txt",
            file_size=len(b"Sample receipt content"),
            file_type="text/plain"
        )
        
        # Initially pending
        self.assertEqual(receipt.status, 'pending')
        
        # Change status to processed
        receipt.status = 'processed'
        receipt.save()
        
        receipt.refresh_from_db()
        self.assertEqual(receipt.status, 'processed')
    
    def test_receipt_file_size_mb_property(self):
        """Test receipt file_size_mb property"""
        receipt = Receipt.objects.create(
            user=self.user,
            file=self.test_file,
            merchant_name="Test Store",
            amount=10.50,
            currency="USD",
            original_file_name="test_receipt.txt",
            file_size=1048576,  # 1 MB in bytes
            file_type="text/plain"
        )
        
        # Check file_size_mb property
        self.assertEqual(receipt.file_size_mb, 1.0)
    
    def test_receipt_save_method(self):
        """Test that save method sets file metadata"""
        # Create receipt without file metadata
        receipt = Receipt(
            user=self.user,
            file=self.test_file,
            merchant_name="Test Store",
            amount=10.50,
            currency="USD"
        )
        
        # Save should set file metadata
        receipt.save()
        
        self.assertEqual(receipt.original_file_name, "test_receipt.txt")
        self.assertEqual(receipt.file_size, len(b"Sample receipt content"))
        self.assertEqual(receipt.file_type, "text/plain")
    
    def test_receipt_without_file_should_fail(self):
        """Test receipt creation without file (should fail)"""
        with self.assertRaises(Exception):
            Receipt.objects.create(
                user=self.user,
                merchant_name="Test Store",  # Missing file
                amount=10.50,
                currency="USD"
            )