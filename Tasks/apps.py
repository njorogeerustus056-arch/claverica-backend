# Tasks/apps.py
from django.apps import AppConfig


class TasksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Tasks'  # matches your folder name
    verbose_name = 'Tasks & Rewards'

    def ready(self):
        """
        Import signals or any startup code for the Tasks app here.
        """
        import Tasks.signals  # ✅ ensures signals are registered
