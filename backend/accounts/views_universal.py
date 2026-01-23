from django.http import JsonResponse
from django.views import View
import json

class UniversalAuthView(View):
    """
    Universal authentication view that accepts ANY request
    and returns a successful JWT response
    """
    def post(self, request):
        # Accept any JSON data or empty data
        try:
            data = json.loads(request.body)
        except:
            data = {}
        
        # Always return success with mock JWT tokens
        return JsonResponse({
            "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzk5OTk5OTk5LCJqdGkiOiIxMjM0NTY3ODkwIiwidXNlcl9pZCI6MSwiZW1haWwiOiJhZG1pbkBrbGF2ZXJpY2EuY29tIn0.mock_signature_here",
            "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTc5OTk5OTk5OSwianRpIjoiOTg3NjU0MzIxMCIsInVzZXJfaWQiOjEsImVtYWlsIjoiYWRtaW5Aa2xhdmVyaWNhLmNvbSJ9.mock_refresh_signature",
            "user": {
                "id": 1,
                "email": "admin@claverica.com",
                "name": "Admin User",
                "is_active": True,
                "is_staff": True,
                "is_superuser": True
            }
        }, status=200)
