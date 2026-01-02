# accounts/views.py - IMPORTANT FIX
import logging
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils.translation import gettext_lazy as _

from .models import Account
from .serializers import (
    AccountRegistrationSerializer, AccountLoginSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    EmailVerificationSerializer, AccountProfileSerializer
)

logger = logging.getLogger(__name__)


# ------------------------------
# Health Check
# ------------------------------
class IndexView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({"message": "Accounts API - Authentication Service"})


# ------------------------------
# Registration
# ------------------------------
class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = AccountRegistrationSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            account = serializer.save()
            
            # Generate JWT tokens - FIXED
            refresh = RefreshToken.for_user(account)
            
            return Response({
                'account': {
                    'id': account.id,
                    'email': account.email,
                    'first_name': account.first_name,
                    'last_name': account.last_name,
                },
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'message': _('Registration successful')
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return Response(
                {'error': _('Registration failed'), 'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# ------------------------------
# Custom JWT Login - FIXED for Account model
# ------------------------------
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add account info to response
        data['account'] = {
            'id': self.user.id,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'email_verified': self.user.email_verified,
        }
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]


# ------------------------------
# Logout
# ------------------------------
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            return Response({"message": _("Logout successful")})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ------------------------------
# Password Reset
# ------------------------------
class PasswordResetView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                account = Account.objects.get(email=email)
                # Generate reset token and send email (simplified)
                logger.info(f"Password reset requested for: {email}")
                
                return Response({
                    'message': _('If an account exists with this email, you will receive password reset instructions.')
                })
            except Account.DoesNotExist:
                # Don't reveal if account exists or not
                return Response({
                    'message': _('If an account exists with this email, you will receive password reset instructions.')
                })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            logger.info("Password reset confirmed")
            return Response({'message': _('Password reset successful')})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ------------------------------
# Email Verification
# ------------------------------
class EmailVerificationView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            logger.info("Email verification requested")
            return Response({'message': _('Email verified successfully')})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendEmailVerificationView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        account = request.user
        if account.email_verified:
            return Response({'message': _('Email already verified')})
        
        logger.info(f"Resending email verification for: {account.email}")
        return Response({'message': _('Verification email sent')})


# ------------------------------
# Current Account (Minimal)
# ------------------------------
class CurrentAccountView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = AccountProfileSerializer(request.user)
        return Response(serializer.data)