from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
# SIMPLEJWT IMPORT PATCHED OUT
from .serializers_fix import DummyAuthSerializer

class CustomTokenObtainPairView(APIView):
    permission_classes = [AllowAny]
    serializer_class = DummyAuthSerializer
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        refresh = RefreshToken.for_user(user)
        refresh['email'] = user.email
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username
            }
        })
