import sys
if "tasks" in sys.modules:
    del sys.modules["tasks"]

# tasks/apps.py
from django.apps import AppConfig


class TasksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.claverica_tasks'
    label = 'claverica_tasks'  # Unique label
    verbose_name = 'backend.claverica_tasks'

    def ready(self):
        """
        Import and connect signals when the app is ready.
        This avoids circular imports.
        """
        # Import signals module to connect the signal handlers
        try:
            from . import signals
            # # from . import signals  # TEMPORARILY DISABLED  # TEMPORARILY DISABLED
            # The import alone connects the signals due to @receiver decorators
        except ImportError as e:
            print(f"Warning: Could not import backend.claverica_tasks.signals: {e}")