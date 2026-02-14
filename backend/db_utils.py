# backend/db_utils.py
"""
Database utility functions to prevent connection leaks and timeouts
"""
import logging
from django.db import connection

logger = logging.getLogger(__name__)

class DatabaseConnectionMiddleware:
    """
    Middleware to close database connections after each request
    This prevents connection leaks that can cause worker timeouts
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process the request and get response
        response = self.get_response(request)
        
        # Close database connection after response
        self.close_connections()
        
        return response
    
    def close_connections(self):
        """Close database connections to prevent timeouts"""
        try:
            connection.close_if_unusable_or_obsolete()
            logger.debug("Database connection checked and closed if needed")
        except Exception as e:
            logger.error(f"Error closing database connection: {e}")

def close_old_connections():
    """
    Function to close old database connections
    Can be called manually in views or tasks
    """
    try:
        connection.close_if_unusable_or_obsolete()
        return True
    except Exception as e:
        logger.error(f"Error in close_old_connections: {e}")
        return False