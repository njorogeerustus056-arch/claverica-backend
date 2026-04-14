# receipts/models.py
import os

from django.conf import settings
from django.db import models


class Receipt(models.Model):
    """
    Represents a financial receipt uploaded by an admin.

    Stores metadata about the receipt along with the PDF file.
    Supports types: Invoice, Refund, and Credit Note.
    """

    TYPE_CHOICES = [
        ("invoice", "Invoice"),
        ("refund", "Refund"),
        ("credit_note", "Credit Note"),
    ]

    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        help_text="Type of receipt document.",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Monetary amount on the receipt (must be > 0).",
    )
    date = models.DateField(
        help_text="Date the receipt was issued.",
    )
    customer_name = models.CharField(
        max_length=255,
        help_text="Full name of the customer.",
    )
    pdf_file = models.FileField(
        upload_to="receipts/",
        help_text="PDF file of the receipt (max 10MB).",
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the receipt was uploaded.",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="uploaded_receipts",
        help_text="Admin user who uploaded this receipt.",
    )

    class Meta:
        ordering = ["-date", "-uploaded_at"]
        verbose_name = "Receipt"
        verbose_name_plural = "Receipts"

    def __str__(self):
        return f"{self.get_type_display()} - {self.customer_name} - {self.amount}"

    def delete(self, *args, **kwargs):
        """Override delete to also remove the PDF file from disk."""
        if self.pdf_file:
            file_path = self.pdf_file.path
            if os.path.isfile(file_path):
                os.remove(file_path)
        super().delete(*args, **kwargs)