# users/apps.py - VERIFY THIS
from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    
    def ready(self):
        # Import signals to ensure they're registered
        try:
            import users.signals
            print("✅ Users signals imported successfully")
        except Exception as e:
            print(f"⚠ Could not import users.signals: {e}")