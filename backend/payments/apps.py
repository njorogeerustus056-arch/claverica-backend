# payments/apps.py - UPDATED

from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class PaymentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.payments'
    
    def ready(self):
        # Signals temporarily disabled during startup
        pass