# transactions/apps.py
from django.apps import AppConfig

class TransactionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'transactions'
    
    def ready(self):
        # Import signals to ensure they're connected
        import transactions.signals
        print(f"[APP] Transactions app ready - signals loaded")