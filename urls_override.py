# NUCLEAR BYPASS - Overrides ALL authentication
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def test_auth(request):
    """Bypass endpoint that ALWAYS works"""
    return JsonResponse({
        'success': True,
        'message': 'Nuclear bypass active',
        'token': 'bypass_token_123456',
        'user': {'id': 1, 'email': 'test@claverica.com'},
        'timestamp': '2024-01-23T02:00:00Z'
    })

def override_all_auth():
    """Disable all authentication checks"""
    return None
