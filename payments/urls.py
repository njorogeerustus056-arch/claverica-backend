from django.urls import path
from django.http import JsonResponse

# Temporary test view
def index(request):
    return JsonResponse({"message": "Payments API working!"})

urlpatterns = [
    path('', index, name='payments_index'),
]
