from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache

@csrf_exempt
@never_cache
def railway_health_check(request):
    """Ultra simple health check - ALWAYS returns 200 OK, never redirects"""
    return HttpResponse("OK", status=200, content_type="text/plain")
