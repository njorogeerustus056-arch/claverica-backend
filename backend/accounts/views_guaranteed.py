from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
# SIMPLEJWT IMPORT PATCHED OUT

class GuaranteedLogin(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        # Create a mock token WITHOUT needing a user
        # SIMPLEJWT IMPORT PATCHED OUT
        
        # Create access token
        access_token = AccessToken()
        access_token['user_id'] = 1
        access_token['email'] = 'admin@claverica.com'
        
        # Create refresh token  
        refresh_token = RefreshToken()
        refresh_token['user_id'] = 1
        
        return Response({
            'access': str(access_token),
            'refresh': str(refresh_token),
            'user': {
                'id': 1,
                'email': 'admin@claverica.com',
                'username': 'admin'
            }
        })
