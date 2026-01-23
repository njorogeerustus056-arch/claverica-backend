from rest_framework.decorators import api_view
from rest_framework.response import Response
import uuid

@api_view(['GET'])
def api_root(request):
    return Response({"api": "Claverica Banking API", "status": "ok"})

@api_view(['GET'])
def kyc_status(request):
    return Response({"status": "verified"})

@api_view(['GET'])
def transactions_list(request):
    return Response({"results": []})

@api_view(['POST'])
def tac_verify(request):
    return Response({"valid": True})
