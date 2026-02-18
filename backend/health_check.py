import time
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db import connections
from django.db.utils import OperationalError

@require_GET
def health_check(request):
    """Health check endpoint with trailing slash"""
    # Check database connection
    db_status = "ok"
    try:
        connections['default'].cursor().execute('SELECT 1')
    except OperationalError:
        db_status = "error"
    
    return JsonResponse({
        "status": "ok",
        "database": db_status,
        "timestamp": time.time()
    })
