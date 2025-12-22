from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Receipt
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

class ReceiptTests(APITestCase):

    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client.force_authenticate(user=self.user)

        # Sample file for upload
        self.file = SimpleUploadedFile(
            "receipt.txt",
            b"Sample receipt content",
            content_type="text/plain"
        )

    def test_upload_receipt(self):
        url = reverse("upload_receipt")
        data = {
            "file": self.file,
            "merchant_name": "Test Store",
            "amount": "10.50",
            "currency": "USD",
            "category": "other",
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("receipt", response.data)
        self.assertEqual(response.data["receipt"]["merchant_name"], "Test Store")
        self.assertEqual(response.data["receipt"]["amount"], "10.50")

    def test_list_receipts(self):
        # Create a receipt
        receipt = Receipt.objects.create(
            user=self.user,
            file=self.file,
            file_name="receipt.txt",
            original_file_name="receipt.txt",
            file_size=self.file.size,
            file_type="text/plain",
            storage_path="receipts/receipt.txt",
            merchant_name="Test Store",
            amount=10.50,
        )
        url = reverse("list_receipts")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["receipts"]), 1)
        self.assertEqual(response.data["receipts"][0]["merchant_name"], "Test Store")

    def test_receipt_detail(self):
        receipt = Receipt.objects.create(
            user=self.user,
            file=self.file,
            file_name="receipt.txt",
            original_file_name="receipt.txt",
            file_size=self.file.size,
            file_type="text/plain",
            storage_path="receipts/receipt.txt",
            merchant_name="Test Store",
            amount=10.50,
        )
        url = reverse("receipt_detail", kwargs={"receipt_id": receipt.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["receipt"]["id"], str(receipt.id))
        self.assertEqual(response.data["receipt"]["merchant_name"], "Test Store")
