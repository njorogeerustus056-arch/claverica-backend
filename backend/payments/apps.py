# payments/apps.py - UPDATED

from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class PaymentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payments'
    
    def ready(self):
        """Initialize the payments application"""
        # Import signals only once to ensure they're connected
        # Check if we're in a management command or running server
        import sys
        
        # Skip signal registration for certain management commands
        if 'manage.py' in sys.argv:
            command = sys.argv[1] if len(sys.argv) > 1 else ''
            # Skip for certain commands that don't need signals
            skip_commands = ['makemigrations', 'migrate', 'collectstatic', 'test']
            if command in skip_commands:
                logger.debug(f"Skipping signal registration for command: {command}")
                return
        
        try:
            # Import and register signals
            import payments.signals
            logger.debug("Payments signals successfully registered")
            
            # Import wallet signals if they exist
            try:
                import payments.wallet_signals
                logger.debug("Wallet signals successfully registered")
            except ImportError:
                logger.debug("No wallet signals found, skipping")
                
        except ImportError as e:
            logger.error(f"Failed to import payments signals: {e}")
        except Exception as e:
            logger.error(f"Error registering payments signals: {e}")