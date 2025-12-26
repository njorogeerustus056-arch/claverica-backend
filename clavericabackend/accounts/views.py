from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.http import JsonResponse
from django.contrib.auth import authenticate
from .models import Account
from .serializers import AccountSerializer

# ------------------------------
# Health / Test Endpoint
# ------------------------------
def index(request):
    return JsonResponse({"message": "Accounts API working!"})

# ------------------------------
# Registration Endpoint
# ------------------------------
class RegisterView(generics.CreateAPIView):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": {
                    "id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                },
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_201_CREATED,
        )


# ------------------------------
# Custom JWT Token Serializer
# ------------------------------
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom serializer that returns user data along with tokens.
    This makes the frontend experience smoother by providing user info
    immediately after login without requiring a separate API call.
    """
    
    def validate(self, attrs):
        # Get the default validated data (access and refresh tokens)
        data = super().validate(attrs)
        
        # Add custom user data to the response
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
        }
        
        return data


# ------------------------------
# Custom Login View with JWT
# ------------------------------
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom login view that:
    1. Uses our custom authentication backend (EmailBackend)
    2. Returns user data along with JWT tokens
    3. Provides clear error messages for debugging
    
    This view accepts {"username": "email@example.com", "password": "..."} 
    from the frontend and handles authentication properly.
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        """
        Override post to provide better error handling and logging.
        """
        try:
            response = super().post(request, *args, **kwargs)
            return response
        except Exception as e:
            # Log the error for debugging (you can use proper logging here)
            print(f"Login error: {str(e)}")
            
            # Return a clear error message
            return Response(
                {
                    "detail": "Unable to log in with provided credentials.",
                    "error": str(e)
                },
                status=status.HTTP_401_UNAUTHORIZED
            )


# ------------------------------
# Alternative: Manual Login View (without Simple JWT's built-in view)
# ------------------------------
class ManualLoginView(generics.GenericAPIView):
    """
    Alternative manual login view if you want more control.
    This directly uses Django's authenticate() function and manually
    generates JWT tokens. Use this if CustomTokenObtainPairView doesn't work.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        # Get credentials from request
        username = request.data.get('username')  # This could be email or username
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {"detail": "Please provide both username/email and password."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Authenticate using our custom backend
        # The 'username' parameter will be handled by EmailBackend
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # User is authenticated, generate tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                }
            }, status=status.HTTP_200_OK)
        else:
            # Authentication failed
            return Response(
                {"detail": "Invalid credentials. Please check your email and password."},
                status=status.HTTP_401_UNAUTHORIZED
            )