from django.http import HttpResponse
import os

def health_check(request):
    """Ultra simple health check - guaranteed 200"""
    return HttpResponse("OK", status=200, content_type="text/plain")

# This ensures the view is loaded at module import
print("=== HEALTH CHECK VIEW LOADED ===")
