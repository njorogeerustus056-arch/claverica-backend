from django.apps import AppConfig

class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"
    
    def ready(self):
        # Import signals to ensure they're connected
        import users.signals
        print(f"[APP] Users app ready - signals loaded")
