from django.apps import AppConfig

class TransfersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.transfers'
    label = 'transfers'
    
    def ready(self):
        # Import signals if needed
        pass
