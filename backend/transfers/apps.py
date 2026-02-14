from django.apps import AppConfig

class TransfersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'transfers'
    
    def ready(self):
        import transfers.signals  # Keep this - now it's correct!