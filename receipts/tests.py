from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Receipt
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

class ReceiptTests(APITestCase):

    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client.force_authenticate(user=self.user)

        # Sample file for upload
        self.file = SimpleUploadedFile("receipt.txt", b"Sample content", content_type="text/plain")

    def test_upload_receipt(self):
        url = reverse("upload_receipt")
        data = {
            "user_id": str(self.user.id),
            "file": self.file,
            "merchant_name": "Test Store",
            "amount": "10.50",
            "currency": "USD",
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("receipt", response.data)

    def test_list_receipts(self):
        # Create a receipt
        receipt = Receipt.objects.create(
            user=self.user,
            file_name="receipt.txt",
            original_file_name="receipt.txt",
            file_size=12,
            file_type="text/plain",
            storage_path="local/receipt.txt"
        )
        url = reverse("list_receipts")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["receipts"]), 1)

    def test_receipt_detail(self):
        receipt = Receipt.objects.create(
            user=self.user,
            file_name="receipt.txt",
            original_file_name="receipt.txt",
            file_size=12,
            file_type="text/plain",
            storage_path="local/receipt.txt"
        )
        url = reverse("receipt_detail", kwargs={"receipt_id": receipt.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["receipt"]["id"], str(receipt.id))
