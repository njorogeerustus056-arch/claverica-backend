"""
Custom middleware for Claverica backend
Request logging and monitoring
"""

import logging
import time
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Log all incoming requests and their processing time.
    Used for monitoring, debugging, and performance analysis.
    """
    
    def process_request(self, request):
        """Record the start time of request processing"""
        request.start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Log request details and processing time"""
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Log the request
            logger.info(
                f"{request.method} {request.path} "
                f"[{response.status_code}] "
                f"{duration:.3f}s "
                f"- {request.META.get('REMOTE_ADDR', 'unknown')}"
            )
        
        return response
    
    def process_exception(self, request, exception):
        """Log exceptions that occur during request processing"""
        logger.error(
            f"Exception in {request.method} {request.path}: "
            f"{type(exception).__name__}: {str(exception)}",
            exc_info=True
        )
        return None
