from django.apps import AppConfig


class TransactionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'transactions'
    verbose_name = 'Transaction Management'
    
    def ready(self):
        """
        Import signals or perform startup tasks when the app is ready.
        """
        # Import any signals here if needed in the future
        # import transactions.signals
        pass
