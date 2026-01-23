from django.apps import AppConfig

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.users'  # Must match what's in INSTALLED_APPS
    label = 'users'
    
    def ready(self):
        # Import signals if needed
        pass
