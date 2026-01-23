from django.contrib import admin
from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponse

@api_view(['POST'])
def emergency_login(request):
    return Response({
        'success': True,
        'message': 'Emergency login active',
        'token': 'emergency-token-123'
    })

@api_view(['GET']) 
def api_root(request):
    return Response({
        'status': 'ok',
        'message': 'Claverica API',
        'endpoints': ['/api/emergency-login/']
    })

@api_view(['GET'])
def transactions_list(request):
    return Response({
        'transactions': [
            {'id': 1, 'amount': 100, 'type': 'deposit'}
        ]
    })

def home(request):
    return HttpResponse("Claverica Banking API")

urlpatterns = [
    path('api/', api_root),
    path('api/emergency-login/', emergency_login),
    path('api/transactions/', transactions_list),
    path('admin/', admin.site.urls),
    path('', home),
]
