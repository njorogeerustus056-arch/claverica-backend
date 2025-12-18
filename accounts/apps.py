# accounts/apps.py
from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        """
        Safely import signals to avoid startup errors if dependencies are missing.
        """
        try:
            import accounts.signals
        except ModuleNotFoundError as e:
            # Log the error instead of raising it
            logger.warning(f"accounts.signals could not be imported: {e}")
        except Exception as e:
            logger.error(f"Unexpected error importing accounts.signals: {e}")
