"""
receipts/tests.py - ENHANCED VERSION WITH MODEL AND API TESTS
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from receipts.models import Receipt
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
import json

User = get_user_model()


# ============ MODEL TESTS ============
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
    
    # ... keep all your existing model test methods ...


# ============ API TESTS ============
class ReceiptAPITests(TestCase):
    """Test cases for Receipt API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='api@example.com',
            password='testpass123',
            first_name='API',
            last_name='Test'
        )
        
        # Create a test file
        self.test_file = SimpleUploadedFile(
            "test_receipt.txt",
            b"Test receipt content for API",
            content_type="text/plain"
        )
        
        # Create test receipts
        self.receipt1 = Receipt.objects.create(
            user=self.user,
            file=self.test_file,
            merchant_name="Test Store 1",
            amount=29.99,
            currency="USD",
            category="shopping",
            original_file_name="test_receipt.txt",
            file_size=len(b"Test receipt content for API"),
            file_type="text/plain",
            notes="Test receipt 1"
        )
        
        self.receipt2 = Receipt.objects.create(
            user=self.user,
            file=self.test_file,
            merchant_name="Test Store 2",
            amount=15.50,
            currency="USD",
            category="food",
            original_file_name="test_receipt.txt",
            file_size=len(b"Test receipt content for API"),
            file_type="text/plain",
            notes="Test receipt 2"
        )
        
        # Authenticate
        self.client.force_authenticate(user=self.user)
    
    def test_list_receipts_api(self):
        """Test GET /api/receipts/list/"""
        response = self.client.get('/api/receipts/list/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('receipts', response.data)
        self.assertIn('pagination', response.data)
        
        # Check receipts count
        self.assertEqual(len(response.data['receipts']), 2)
        
        # Check pagination
        pagination = response.data['pagination']
        self.assertEqual(pagination['total'], 2)
        self.assertEqual(pagination['current_page'], 1)
    
    def test_list_receipts_with_filters(self):
        """Test GET /api/receipts/list/ with category filter"""
        response = self.client.get('/api/receipts/list/?category=food')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['receipts']), 1)
        self.assertEqual(response.data['receipts'][0]['category'], 'food')
    
    def test_get_receipt_detail_api(self):
        """Test GET /api/receipts/<uuid>/"""
        response = self.client.get(f'/api/receipts/{self.receipt1.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('receipt', response.data)
        receipt = response.data['receipt']
        
        self.assertEqual(receipt['id'], str(self.receipt1.id))
        self.assertEqual(receipt['merchant_name'], 'Test Store 1')
        self.assertEqual(receipt['amount'], '29.99')
        self.assertEqual(receipt['category'], 'shopping')
    
    def test_get_nonexistent_receipt_detail(self):
        """Test GET /api/receipts/<uuid>/ with non-existent receipt"""
        import uuid
        fake_uuid = uuid.uuid4()
        response = self.client.get(f'/api/receipts/{fake_uuid}/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
    
    def test_upload_receipt_api(self):
        """Test POST /api/receipts/upload/"""
        # Create a new test file
        upload_file = SimpleUploadedFile(
            "upload_test.txt",
            b"New receipt content",
            content_type="text/plain"
        )
        
        data = {
            'merchant_name': 'New Store',
            'amount': '49.99',
            'currency': 'USD',
            'category': 'business',
            'notes': 'Business expense upload'
        }
        
        response = self.client.post(
            '/api/receipts/upload/',
            {'file': upload_file, **data},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('receipt', response.data)
        
        receipt = response.data['receipt']
        self.assertEqual(receipt['merchant_name'], 'New Store')
        self.assertEqual(receipt['amount'], '49.99')
        self.assertEqual(receipt['category'], 'business')
        
        # Verify it was saved to database
        receipt_id = receipt['id']
        db_receipt = Receipt.objects.get(id=receipt_id)
        self.assertEqual(db_receipt.user, self.user)
        self.assertEqual(str(db_receipt.amount), '49.99')
    
    def test_upload_receipt_invalid_data(self):
        """Test POST /api/receipts/upload/ with invalid data"""
        response = self.client.post(
            '/api/receipts/upload/',
            {'file': self.test_file},  # Missing required fields
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_update_receipt_api(self):
        """Test PATCH /api/receipts/<uuid>/update/"""
        update_data = {
            'merchant_name': 'Updated Store Name',
            'amount': '39.99',
            'notes': 'Updated notes for receipt',
            'status': 'processed'
        }
        
        response = self.client.patch(
            f'/api/receipts/{self.receipt1.id}/update/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Verify updates in database
        self.receipt1.refresh_from_db()
        self.assertEqual(self.receipt1.merchant_name, 'Updated Store Name')
        self.assertEqual(str(self.receipt1.amount), '39.99')
        self.assertEqual(self.receipt1.status, 'processed')
    
    def test_update_nonexistent_receipt(self):
        """Test PATCH /api/receipts/<uuid>/update/ with non-existent receipt"""
        import uuid
        fake_uuid = uuid.uuid4()
        
        update_data = {'merchant_name': 'Updated'}
        response = self.client.patch(
            f'/api/receipts/{fake_uuid}/update/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_delete_receipt_api(self):
        """Test DELETE /api/receipts/<uuid>/delete/"""
        # Create a receipt to delete
        delete_receipt = Receipt.objects.create(
            user=self.user,
            file=self.test_file,
            merchant_name="To Delete",
            amount=10.00,
            currency="USD",
            original_file_name="test_receipt.txt",
            file_size=len(b"Test receipt content for API"),
            file_type="text/plain"
        )
        
        response = self.client.delete(f'/api/receipts/{delete_receipt.id}/delete/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Verify it was deleted
        with self.assertRaises(Receipt.DoesNotExist):
            Receipt.objects.get(id=delete_receipt.id)
    
    def test_get_receipt_stats_api(self):
        """Test GET /api/receipts/stats/"""
        response = self.client.get('/api/receipts/stats/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_receipts', response.data)
        self.assertIn('total_amount', response.data)
        self.assertIn('categories', response.data)
        self.assertIn('status_breakdown', response.data)
        self.assertIn('monthly_stats', response.data)
        
        # Check stats values
        self.assertEqual(response.data['total_receipts'], 2)
        self.assertEqual(response.data['currency'], 'USD')
        
        # Check category stats
        categories = response.data['categories']
        self.assertIn('shopping', categories)
        self.assertIn('food', categories)
    
    def test_unauthenticated_access(self):
        """Test API endpoints without authentication"""
        self.client.force_authenticate(user=None)  # Log out
        
        # Test list endpoint
        response = self.client.get('/api/receipts/list/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test stats endpoint
        response = self.client.get('/api/receipts/stats/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_access_other_users_receipt(self):
        """Test accessing another user's receipt (should fail)"""
        # Create another user
        other_user = User.objects.create_user(
            email='other@example.com',
            password='otherpass123',
            first_name='Other',
            last_name='User'
        )
        
        # Create receipt for other user
        other_receipt = Receipt.objects.create(
            user=other_user,
            file=self.test_file,
            merchant_name="Other User Store",
            amount=99.99,
            currency="USD",
            original_file_name="test_receipt.txt",
            file_size=len(b"Test receipt content for API"),
            file_type="text/plain"
        )
        
        # Try to access other user's receipt
        response = self.client.get(f'/api/receipts/{other_receipt.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Try to update other user's receipt
        response = self.client.patch(
            f'/api/receipts/{other_receipt.id}/update/',
            data=json.dumps({'merchant_name': 'Hacked'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)