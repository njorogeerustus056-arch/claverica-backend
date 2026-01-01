# accounts/apps.py
from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        """
        Import signals when app is ready
        """
        try:
            import accounts.signals
        except ModuleNotFoundError as e:
            logger.warning(f"accounts.signals could not be imported: {e}")
        except Exception as e:
            logger.error(f"Unexpected error importing accounts.signals: {e}")