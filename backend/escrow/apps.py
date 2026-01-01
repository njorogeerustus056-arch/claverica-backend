from django.apps import AppConfig


class EscrowConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'escrow'
    verbose_name = 'Escrow Management'
    
    def ready(self):
        """
        Import signals or perform startup tasks when the app is ready.
        """
        # Import signals to ensure they're connected
        import escrow.signals