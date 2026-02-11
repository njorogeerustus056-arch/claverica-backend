from django.http import HttpResponse

def railway_health_check(request):
    """Ultra simple health check - NO DATABASE, NO DJANGO, just pure HTTP"""
    return HttpResponse("OK", status=200, content_type="text/plain")
