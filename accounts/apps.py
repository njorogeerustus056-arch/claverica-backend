# accounts/apps.py
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        # Import signals safely
        try:
            import accounts.signals
        except ImportError as e:
            # Log the error or pass silently in dev environment
            print(f"Could not import accounts.signals: {e}")
