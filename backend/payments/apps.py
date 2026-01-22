from django.apps import AppConfig

class PaymentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.payments'
    verbose_name = 'Payments'
    
    def ready(self):
        # Import signals here if needed
        pass
