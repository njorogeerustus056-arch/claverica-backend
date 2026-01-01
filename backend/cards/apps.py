"""
cards/apps.py
"""

from django.apps import AppConfig


class CardsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cards'
    verbose_name = 'Cards Management'
    
    def ready(self):
        """Import signals when app is ready"""
        try:
            import cards.signals  # noqa
        except ImportError:
            pass