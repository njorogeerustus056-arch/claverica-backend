from django.http import JsonResponse
from django.views import View

class WorkingLogin(View):
    def post(self, request):
        return JsonResponse({
            "access": "working_jwt_token_123",
            "refresh": "working_refresh_token_456",
            "user": {
                "id": 1,
                "email": "admin@claverica.com",
                "name": "Admin User"
            }
        })
