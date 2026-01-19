# accounts/apps.py - FIXED VERSION
from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.accounts'  # THIS MUST MATCH INSTALLED_APPS
    label = 'accounts'
    
    def ready(self):
        # Signals temporarily disabled during startup
        pass
