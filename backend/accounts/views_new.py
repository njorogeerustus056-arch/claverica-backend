from django.http import JsonResponse
from django.views import View
import json

class NewLogin(View):
    def post(self, request):
        return JsonResponse({
            "access": "new_endpoint_works_123",
            "refresh": "new_refresh_456",
            "user": {"id": 1, "email": "admin@claverica.com"}
        })
