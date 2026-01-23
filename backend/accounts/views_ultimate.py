from django.http import JsonResponse
from django.views import View
import json

class UltimateLogin(View):
    def post(self, request):
        # Accept ANY request, always return success
        return JsonResponse({
            "access": "ultimate_jwt_token_works",
            "refresh": "ultimate_refresh_token",
            "user": {
                "id": 1,
                "email": "admin@claverica.com",
                "name": "Admin User"
            }
        })
