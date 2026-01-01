# tasks/apps.py
from django.apps import AppConfig


class TasksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tasks'
    verbose_name = 'Tasks & Rewards'

    def ready(self):
        """
        Import and connect signals when the app is ready.
        This avoids circular imports.
        """
        # Import signals module to connect the signal handlers
        try:
            from . import signals
            # The import alone connects the signals due to @receiver decorators
        except ImportError as e:
            print(f"Warning: Could not import tasks.signals: {e}")