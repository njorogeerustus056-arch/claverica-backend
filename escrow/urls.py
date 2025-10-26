from django.urls import path
from django.http import JsonResponse

# Temporary test view for escrow API
def index(request):
    return JsonResponse({"message": "Escrow API working!"})

urlpatterns = [
    path('', index, name='escrow_index'),
]
