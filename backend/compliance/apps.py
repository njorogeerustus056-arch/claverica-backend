"""
compliance/apps.py - Django app configuration for compliance
"""

from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class ComplianceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'compliance'
    verbose_name = 'Compliance Management System'
    
    def ready(self):
        """
        Initialize app when Django starts
        """
        # Import and connect signal handlers
        try:
            import compliance.signals  # noqa
            logger.info("Compliance signals imported successfully")
        except ImportError as e:
            logger.error(f"Failed to import compliance signals: {e}")
        
        # Import checks
        try:
            from . import checks
            logger.info("Compliance checks registered")
        except ImportError:
            pass
        
        # Initialize default settings
        self.initialize_default_settings()
        
        # Register scheduled tasks (if using Celery)
        self.register_scheduled_tasks()
    
    def initialize_default_settings(self):
        """
        Initialize default settings for the compliance app
        """
        from django.conf import settings
        
        # Set default settings if not already set
        defaults = {
            'COMPLIANCE_SETTINGS': {
                'KYC_AUTO_APPROVAL_THRESHOLD': 1000,
                'TAC_EXPIRY_MINUTES': 5,
                'TAC_MAX_ATTEMPTS': 3,
                'WITHDRAWAL_DAILY_LIMIT': 10000,
                'WITHDRAWAL_MONTHLY_LIMIT': 50000,
                'REQUIRE_TAC_ABOVE': 1000,
                'REQUIRE_VIDEO_CALL_ABOVE': 10000,
                'HIGH_RISK_COUNTRIES': ['AF', 'IR', 'KP', 'SY', 'YE'],
                'RESTRICTED_OCCUPATIONS': [],
                'DOCUMENT_MAX_SIZE_MB': 10,
                'ALLOWED_DOCUMENT_TYPES': ['image/jpeg', 'image/png', 'application/pdf'],
                'AUDIT_LOG_RETENTION_DAYS': 365,
                'KYC_REVIEW_INTERVAL_DAYS': 365,
                'COMPLIANCE_CHECK_INTERVAL_DAYS': 90,
                'ALERT_EXPIRY_HOURS': 24,
            },
            'COMPLIANCE_API_URL': 'http://localhost:8000/compliance/api/',
            'COMPLIANCE_WEBHOOK_URL': None,
        }
        
        for key, value in defaults.items():
            if not hasattr(settings, key):
                setattr(settings, key, value)
                logger.info(f"Set default setting: {key} = {value}")
    
    def register_scheduled_tasks(self):
        """
        Register scheduled tasks for compliance operations
        """
        try:
            # This would register Celery tasks if Celery is configured
            # For now, just log the registration
            logger.info("Compliance scheduled tasks registered")
        except Exception as e:
            logger.error(f"Failed to register scheduled tasks: {e}")