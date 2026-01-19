from django.http import JsonResponse
from django.views import View
import json

class HealthCheckView(View):
    def get(self, request):
        return JsonResponse({
            'status': 'healthy',
            'backend': 'Claverica Backend',
            'apps': ['accounts', 'users', 'transfers', 'payments'],
            'note': 'Running without database migrations (temporarily)'
        })

class TestTransferView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            return JsonResponse({
                'success': True,
                'message': 'Transfer endpoint works',
                'received_data': data
            })
        except:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON'
            }, status=400)
