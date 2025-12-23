"""
Backend App Configuration
"""

from django.apps import AppConfig


class BackendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend'
    verbose_name = 'Claverica Backend'
    
    def ready(self):
        """
        Runs when Django starts.
        Import signals or run startup code here.
        """
        pass
