# accounts/views.py - UPDATED COMPLETELY
import logging
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .models import Account
from .utils.email_service import EmailService
from .serializers import (
    AccountRegistrationSerializer, AccountLoginSerializer,
    EmailVerificationOTPSerializer, PasswordResetRequestSerializer,
    PasswordResetOTPVerifySerializer, PasswordResetConfirmSerializer,
    AccountProfileSerializer
)

logger = logging.getLogger(__name__)


# ------------------------------
# Throttle Classes
# ------------------------------
class StrictAnonThrottle(AnonRateThrottle):
    rate = '5/hour'  # Stricter for security endpoints


class ModerateAnonThrottle(AnonRateThrottle):
    rate = '10/hour'


# ------------------------------
# Health Check
# ------------------------------
class IndexView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({"message": "Accounts API - Authentication Service"})


# ------------------------------
# Registration with OTP
# ------------------------------
class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = AccountRegistrationSerializer
    throttle_classes = [ModerateAnonThrottle]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Check if email already exists
            email = serializer.validated_data['email']
            if Account.objects.filter(email=email).exists():
                return Response(
                    {'error': _('Email already registered')},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            account = serializer.save()
            
            # Generate and send OTP for email verification
            otp = account.generate_email_verification_otp()
            
            # Send OTP email
            email_sent = EmailService.send_otp_email(
                to_email=account.email,
                otp=otp,
                purpose='verification'
            )
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(account)
            
            response_data = {
                'account': {
                    'id': account.id,
                    'email': account.email,
                    'first_name': account.first_name,
                    'last_name': account.last_name,
                    'email_verified': account.email_verified,
                },
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'message': _('Registration successful. Please verify your email.'),
                'otp_sent': email_sent,
            }
            
            if not email_sent:
                response_data['warning'] = _('Failed to send verification email. Please try resending.')
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return Response(
                {'error': _('Registration failed'), 'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# ------------------------------
# Email Verification with OTP
# ------------------------------
class VerifyEmailOTPView(APIView):
    """Verify email using OTP"""
    permission_classes = [AllowAny]
    throttle_classes = [StrictAnonThrottle]
    
    def post(self, request):
        serializer = EmailVerificationOTPSerializer(data=request.data)
        
        if serializer.is_valid():
            account = serializer.validated_data['account']
            
            # Verify the OTP
            if account.is_otp_valid(serializer.validated_data['otp'], 'email_verification'):
                # Mark email as verified
                account.email_verified = True
                account.clear_otp('email_verification')
                account.save(update_fields=['email_verified'])
                
                # ✅ ADDED: Generate new JWT tokens after successful verification
                refresh = RefreshToken.for_user(account)
                
                # Send welcome email
                EmailService.send_welcome_email(account.email, account.first_name)
                
                return Response({
                    'success': True,
                    'message': _('Email verified successfully!'),
                    'account': {
                        'id': account.id,
                        'email': account.email,
                        'first_name': account.first_name,
                        'last_name': account.last_name,
                        'email_verified': account.email_verified,
                    },
                    # ✅ ADDED: Return JWT tokens for immediate login
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                })
            else:
                return Response({
                    'error': _('Invalid or expired OTP')
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendVerificationOTPView(APIView):
    """Resend verification OTP"""
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    
    def post(self, request):
        account = request.user
        
        if account.email_verified:
            return Response({
                'message': _('Email already verified')
            })
        
        # Check if OTP was sent recently (rate limiting)
        if account.email_verification_otp_sent_at:
            time_since_last_otp = timezone.now() - account.email_verification_otp_sent_at
            if time_since_last_otp.total_seconds() < 60:  # 1 minute cooldown
                return Response({
                    'error': _('Please wait before requesting another OTP')
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Generate and send new OTP
        otp = account.generate_email_verification_otp()
        email_sent = EmailService.send_otp_email(
            to_email=account.email,
            otp=otp,
            purpose='verification'
        )
        
        if email_sent:
            return Response({
                'message': _('Verification OTP sent to your email'),
                'email': account.email,
                'cooldown_seconds': 60
            })
        else:
            return Response({
                'error': _('Failed to send OTP email. Please try again.')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ------------------------------
# Password Reset with OTP
# ------------------------------
class PasswordResetRequestView(APIView):
    """Request password reset - sends OTP"""
    permission_classes = [AllowAny]
    throttle_classes = [StrictAnonThrottle]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                account = Account.objects.get(email=email)
                
                # Check if OTP was sent recently
                if account.password_reset_otp_sent_at:
                    time_since_last_otp = timezone.now() - account.password_reset_otp_sent_at
                    if time_since_last_otp.total_seconds() < 60:  # 1 minute cooldown
                        return Response({
                            'message': _('Password reset OTP already sent. Please check your email.'),
                            'cooldown_seconds': 60
                        })
                
                # Generate and send OTP
                otp = account.generate_password_reset_otp()
                email_sent = EmailService.send_otp_email(
                    to_email=account.email,
                    otp=otp,
                    purpose='password_reset'
                )
                
                if email_sent:
                    return Response({
                        'message': _('Password reset OTP sent to your email'),
                        'email': account.email,
                        'cooldown_seconds': 60
                    })
                else:
                    return Response({
                        'error': _('Failed to send OTP. Please try again.')
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
            except Account.DoesNotExist:
                # Don't reveal if account exists
                return Response({
                    'message': _('If an account exists with this email, you will receive password reset instructions.')
                })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetVerifyOTPView(APIView):
    """Verify OTP for password reset"""
    permission_classes = [AllowAny]
    throttle_classes = [StrictAnonThrottle]
    
    def post(self, request):
        serializer = PasswordResetOTPVerifySerializer(data=request.data)
        
        if serializer.is_valid():
            account = serializer.validated_data['account']
            
            return Response({
                'success': True,
                'message': _('OTP verified successfully'),
                'email': account.email,
                'token': 'valid'  # In production, you might return a temp token
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """Complete password reset with OTP verification"""
    permission_classes = [AllowAny]
    throttle_classes = [StrictAnonThrottle]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        
        if serializer.is_valid():
            account = serializer.validated_data['account']
            new_password = serializer.validated_data['new_password']
            
            # Set new password
            account.set_password(new_password)
            account.clear_otp('password_reset')
            account.save(update_fields=['password'])
            
            # Send confirmation email
            EmailService.send_password_changed_email(account.email, account.first_name)
            
            return Response({
                'success': True,
                'message': _('Password reset successful. You can now login with your new password.')
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ------------------------------
# Custom JWT Login
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
    throttle_classes = [StrictAnonThrottle]


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
# Current Account
# ------------------------------
class CurrentAccountView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = AccountProfileSerializer(request.user)
        return Response(serializer.data)