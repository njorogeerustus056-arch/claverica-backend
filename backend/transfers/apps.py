"""
transfers/apps.py - Updated app config
"""

from django.apps import AppConfig


class TransfersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.transfers'
    
    def ready(self):
        # Signals temporarily disabled during startup
        pass