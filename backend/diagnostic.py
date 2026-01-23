from django.http import JsonResponse
from django.views import View
import sys

class DiagnosticView(View):
    def get(self, request):
        info = {
            "python_version": sys.version,
            "wsgi_module": str(sys.modules.get('backend.wsgi', 'NOT FOUND')),
            "wsgi_application": str(getattr(sys.modules.get('backend.wsgi', None), 'application', 'NOT FOUND')),
            "django_loaded": 'django' in sys.modules,
            "path": sys.path[:3],
        }
        return JsonResponse(info)
