# accounts/apps.py
from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    
    def ready(self):
        try:
            import accounts.signals
        except ImportError as e:
            logger.warning(f"Could not import accounts.signals: {e}")