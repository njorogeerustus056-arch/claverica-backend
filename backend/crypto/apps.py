from django.apps import AppConfig


class CryptoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.crypto'
    verbose_name = 'Cryptocurrency Management'
    
    def ready(self):
        # Signals temporarily disabled during startup
        pass