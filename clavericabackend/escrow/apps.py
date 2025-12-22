from django.apps import AppConfig


class EscrowConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'escrow'
    verbose_name = 'Escrow Management'
    
    def ready(self):
        """
        Import signals or perform startup tasks when the app is ready.
        """
        # Import any signals here if needed in the future
        # import escrow.signals
        pass
