from django.apps import AppConfig


class EscrowConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.escrow'
    verbose_name = 'Escrow Management'
    
    def ready(self):
        # Signals temporarily disabled during startup
        pass