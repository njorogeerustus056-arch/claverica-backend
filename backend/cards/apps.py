"""
cards/apps.py
"""

from django.apps import AppConfig


class CardsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.cards'
    verbose_name = 'Cards Management'
    
    def ready(self):
        # Signals temporarily disabled during startup
        pass