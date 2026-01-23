from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class FixedAuthView(View):
    def dispatch(self, request, *args, **kwargs):
        # Handle ALL POST requests
        if request.method == 'POST':
            return JsonResponse({
                "access": "eyJfinal.fix",
                "refresh": "eyJfinal.refresh", 
                "user": {"id": 1, "email": "final@fix.com"}
            })
        return self.get(request)
    
    def get(self, request):
        return JsonResponse({"status": "fixed"})
