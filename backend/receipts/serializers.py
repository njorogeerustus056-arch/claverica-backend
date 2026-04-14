# receipts/serializers.py
from datetime import date

from django.utils.timezone import now
from rest_framework import serializers

from .models import Receipt

MAX_PDF_SIZE_BYTES = 10 * 1024 * 1024  # 10MB


class ReceiptSerializer(serializers.ModelSerializer):
    """
    Read serializer for listing and retrieving receipts.

    Includes human-readable type label, uploader email,
    and a direct download URL for the PDF.
    """

    type_display = serializers.CharField(source="get_type_display", read_only=True)
    uploaded_by = serializers.SerializerMethodField()
    pdf_url = serializers.SerializerMethodField()

    class Meta:
        model = Receipt
        fields = [
            "id",
            "type",
            "type_display",
            "amount",
            "date",
            "customer_name",
            "pdf_url",
            "uploaded_at",
            "uploaded_by",
        ]
        read_only_fields = fields

    def get_uploaded_by(self, obj):
        """Return the email of the admin who uploaded the receipt."""
        if obj.uploaded_by:
            return getattr(obj.uploaded_by, "email", str(obj.uploaded_by))
        return None

    def get_pdf_url(self, obj):
        """Return the download endpoint URL for the PDF."""
        request = self.context.get("request")
        url = f"/api/receipts/{obj.id}/download/"
        if request:
            return request.build_absolute_uri(url)
        return url


class ReceiptUploadSerializer(serializers.ModelSerializer):
    """
    Write serializer for admin PDF upload.

    Validates:
      - pdf_file: must be PDF, max 10MB
      - amount: must be greater than 0
      - date: must not be in the future
    """

    class Meta:
        model = Receipt
        fields = ["type", "amount", "date", "customer_name", "pdf_file"]

    def validate_pdf_file(self, value):
        """Ensure the uploaded file is a PDF and within size limit."""
        # Check file extension
        name = value.name.lower()
        if not name.endswith(".pdf"):
            raise serializers.ValidationError("Only PDF files are allowed.")

        # Check content type
        content_type = getattr(value, "content_type", "")
        if content_type and content_type not in ("application/pdf", "application/x-pdf"):
            raise serializers.ValidationError(
                f"Invalid content type '{content_type}'. Must be application/pdf."
            )

        # Check file size
        if value.size > MAX_PDF_SIZE_BYTES:
            size_mb = value.size / (1024 * 1024)
            raise serializers.ValidationError(
                f"File size {size_mb:.1f}MB exceeds the 10MB limit."
            )

        return value

    def validate_amount(self, value):
        """Ensure amount is positive."""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0.")
        return value

    def validate_date(self, value):
        """Ensure the receipt date is not in the future."""
        if value > date.today():
            raise serializers.ValidationError("Receipt date cannot be in the future.")
        return value

    def validate_customer_name(self, value):
        """Strip whitespace and ensure customer name is not blank."""
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Customer name cannot be blank.")
        return value