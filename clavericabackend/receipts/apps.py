from django.apps import AppConfig


class ReceiptsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'receipts'
    verbose_name = 'Receipt Management'
    
    def ready(self):
        """
        Import signals or perform startup tasks when the app is ready.
        """
        # Import any signals here if needed in the future
        # import receipts.signals
        pass
