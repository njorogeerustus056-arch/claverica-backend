from django.apps import AppConfig

class TransactionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.transactions'
    label = 'transactions'
    
    def ready(self):
        # Import signals if needed
        pass
