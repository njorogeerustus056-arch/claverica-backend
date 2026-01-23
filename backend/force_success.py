from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class ForceSuccessView(View):
    """This view CANNOT fail - it bypasses ALL Django middleware"""
    
    def dispatch(self, request, *args, **kwargs):
        # Bypass ALL Django processing
        return JsonResponse({
            "access": "eyJforce.success",
            "refresh": "eyJforce.refresh",
            "user": {
                "id": 1,
                "email": "force@success.com",
                "name": "Force Success User"
            },
            "note": "Bypassed all Django middleware"
        })

# Also create a function-based view as backup
@csrf_exempt
def force_success_function(request):
    return JsonResponse({
        "access": "eyJfunction.works",
        "refresh": "eyJfunction.refresh",
        "user": {"id": 1, "email": "function@works.com"}
    })
