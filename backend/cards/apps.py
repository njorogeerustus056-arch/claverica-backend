# backend/cards/apps.py - UPDATED
from django.apps import AppConfig

class CardsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "cards"
    
    def ready(self):
        # Import signals to ensure they are registered
        import cards.signals