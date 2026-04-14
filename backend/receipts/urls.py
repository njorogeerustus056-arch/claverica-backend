# receipts/urls.py
from django.urls import path, re_path

from .views import (
    ReceiptCreateView,
    ReceiptDeleteView,
    ReceiptDetailView,
    ReceiptDownloadView,
    ReceiptListView,
)

app_name = "receipts"

urlpatterns = [
    # List all receipts - matches both with and without trailing slash
    re_path(r'^/?$', ReceiptListView.as_view(), name="receipt-list"),

    # Upload a new receipt (admin only)
    path("upload/", ReceiptCreateView.as_view(), name="receipt-upload"),

    # Retrieve single receipt metadata
    path("<int:pk>/", ReceiptDetailView.as_view(), name="receipt-detail"),

    # Download the PDF file
    path("<int:pk>/download/", ReceiptDownloadView.as_view(), name="receipt-download"),

    # Delete a receipt (admin only)
    path("<int:pk>/delete/", ReceiptDeleteView.as_view(), name="receipt-delete"),
]