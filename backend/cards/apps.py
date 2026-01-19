from django.apps import AppConfig

class CardsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.cards'
    label = 'cards'
    
    def ready(self):
        # Import signals if needed
        pass
