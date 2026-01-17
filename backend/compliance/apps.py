"""
compliance/apps.py - Django app configuration for compliance
"""

from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class ComplianceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.compliance'
    verbose_name = 'Compliance Management System'
    
    def ready(self):
        # Signals temporarily disabled during startup
        pass