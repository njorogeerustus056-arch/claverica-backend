from django.contrib import admin
from django.urls import path
from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['POST'])
def emergency_login(request):
    return Response({
        'success': True,
        'message': 'Emergency login active',
        'token': 'emergency-token-123'
    })

def home(request):
    return HttpResponse("Claverica Backend - EMERGENCY MODE")

urlpatterns = [
    path('api/emergency-login/', emergency_login),
    path('', home),
    path('admin/', admin.site.urls),
]
