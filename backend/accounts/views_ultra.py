from django.http import HttpResponse
import json

def ultra_login(request):
    if request.method == 'POST':
        response_data = {
            "access": "ultra_simple_token_always_works",
            "refresh": "ultra_refresh_token",
            "user": {
                "id": 1,
                "email": "admin@claverica.com",
                "name": "Admin User"
            }
        }
        return HttpResponse(
            json.dumps(response_data),
            content_type='application/json',
            status=200
        )
    return HttpResponse('Method not allowed', status=405)
