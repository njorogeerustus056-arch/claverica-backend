from django.http import HttpResponse

def railway_health_check(request):
    """Ultra simple health check - ALWAYS returns 200 OK"""
    return HttpResponse("OK", status=200, content_type="text/plain")
