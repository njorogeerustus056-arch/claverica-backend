# receipts/apps.py
from django.apps import AppConfig


class ReceiptsConfig(AppConfig):
    """Configuration for the receipts application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "receipts"