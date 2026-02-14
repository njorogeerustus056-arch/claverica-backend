import logging
import threading
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth import update_session_auth_hash
from django.utils.crypto import get_random_string

from .models import Account
from .serializers import (
    AccountRegistrationSerializer,
    ActivationSerializer,
    ResendActivationSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
    PasswordChangeSerializer
)
from .utils.email_service import EmailService

logger = logging.getLogger(__name__)

# ========== EXISTING VIEWS ==========

class RegisterView(APIView):
    """Register new account and send activation code"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AccountRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            account = serializer.save()

            # Send activation email in background thread to prevent worker timeout
            thread = threading.Thread(
                target=self.send_activation_email,
                args=(account.email, account.activation_code)
            )
            thread.daemon = True
            thread.start()

            return Response({
                'success': True,
                'message': 'Registration successful. Please check your email for activation code.',
                'email': account.email,
                'note': f'For testing, your activation code is: {account.activation_code}',
                'account': {
                    'email': account.email,
                    'first_name': account.first_name,
                    'last_name': account.last_name,
                    'is_active': account.is_active,
                    'is_verified': account.is_verified
                }
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def send_activation_email(self, email, activation_code):
        """Send activation code email (runs in background thread)"""
        subject = 'Activate Your Account - Claverica'
        message = f"""
Thank you for registering with Claverica!

Your activation code is: {activation_code}

Enter this code on our website to activate your account.
This code expires in 24 hours.

If you didn't create an account, please ignore this email.

Best regards,
The Claverica Team
"""

        try:
            send_mail(
                subject,
                message.strip(),
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=True,
            )
            logger.info(f"Activation email sent to {email}")
        except Exception as e:
            logger.warning(f"Email sending failed (but registration succeeded): {e}")


class ActivateView(APIView):
    """Activate account with code"""
    permission_classes = [AllowAny]

    def post(self, request):
        from rest_framework_simplejwt.tokens import RefreshToken

        serializer = ActivationSerializer(data=request.data)
        if serializer.is_valid():
            account = serializer.validated_data['account']
            activation_code = serializer.validated_data['activation_code']

            # Verify activation code
            success, message = account.verify_activation_code(activation_code)

            if success:
                # Generate JWT tokens
                refresh = RefreshToken.for_user(account)

                return Response({
                    'success': True,
                    'message': message,
                    'account': {
                        'email': account.email,
                        'first_name': account.first_name,
                        'last_name': account.last_name,
                        'account_number': account.account_number,
                        'is_verified': account.is_verified,
                        'is_active': account.is_active
                    },
                    'tokens': {
                        'access': str(refresh.access_token),
                        'refresh': str(refresh)
                    }
                })
            else:
                return Response({
                    'success': False,
                    'message': message
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendActivationView(APIView):
    """Resend activation code"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResendActivationSerializer(data=request.data)
        if serializer.is_valid():
            account = serializer.validated_data['email']

            # Generate new activation code
            new_code = account.generate_activation_code()

            # Send new activation email in background thread
            thread = threading.Thread(
                target=self.send_activation_email,
                args=(account.email, new_code)
            )
            thread.daemon = True
            thread.start()

            return Response({
                'success': True,
                'message': 'New activation code sent to your email.',
                'email': account.email,
                'note': f'For testing, new activation code is: {new_code}'
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def send_activation_email(self, email, activation_code):
        """Send activation code email (runs in background thread)"""
        subject = 'New Activation Code - Claverica'
        message = f"""
You requested a new activation code.

Your new activation code is: {activation_code}

Enter this code on our website to activate your account.
This code expires in 24 hours.

Best regards,
The Claverica Team
"""

        try:
            send_mail(
                subject,
                message.strip(),
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=True,
            )
            logger.info(f"Resent activation email to {email}")
        except Exception as e:
            logger.warning(f"Email sending failed (but resend succeeded): {e}")


class LoginView(APIView):
    """Login with email and password"""
    permission_classes = [AllowAny]

    def post(self, request):
        from rest_framework_simplejwt.tokens import RefreshToken

        email = request.data.get('email', '').strip().lower()
        password = request.data.get('password', '')

        if not email or not password:
            return Response({
                'success': False,
                'message': 'Email and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get account by email
            account = Account.objects.get(email=email)

            # Check password
            if not account.check_password(password):
                return Response({
                    'success': False,
                    'message': 'Invalid email or password'
                }, status=status.HTTP_401_UNAUTHORIZED)

            # Check if account is active
            if not account.is_active:
                return Response({
                    'success': False,
                    'message': 'Account is inactive. Please contact support.'
                }, status=status.HTTP_403_FORBIDDEN)

            # Check if account is verified
            if not account.is_verified:
                return Response({
                    'success': False,
                    'message': 'Please verify your email before logging in.'
                }, status=status.HTTP_403_FORBIDDEN)

            # Generate JWT tokens
            refresh = RefreshToken.for_user(account)

            return Response({
                'success': True,
                'message': 'Login successful',
                'account': {
                    'email': account.email,
                    'first_name': account.first_name,
                    'last_name': account.last_name,
                    'account_number': account.account_number,
                    'phone': account.phone,
                    'is_verified': account.is_verified,
                    'is_active': account.is_active
                },
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                }
            }, status=status.HTTP_200_OK)

        except Account.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Invalid email or password'
            }, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.error(f"Login error for {email}: {e}")
            return Response({
                'success': False,
                'message': f'Login error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========== NEW PASSWORD VIEWS ==========

class PasswordResetView(APIView):
    """Request password reset email"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']

            try:
                account = Account.objects.get(email=email)

                # Generate OTP for password reset
                reset_otp = get_random_string(6, '0123456789')
                account.activation_code = reset_otp
                account.activation_code_sent_at = timezone.now()
                account.activation_code_expires_at = timezone.now() + timezone.timedelta(minutes=10)
                account.save(update_fields=['activation_code', 'activation_code_sent_at', 'activation_code_expires_at'])

                # Send password reset email in background thread
                thread = threading.Thread(
                    target=EmailService.send_otp_email,
                    args=(email, reset_otp, 'password_reset')
                )
                thread.daemon = True
                thread.start()

                return Response({
                    'success': True,
                    'message': 'Password reset OTP sent to your email',
                    'email': email,
                    'note': f'For testing, your OTP is: {reset_otp}'
                }, status=status.HTTP_200_OK)

            except Account.DoesNotExist:
                # Still return success to prevent email enumeration
                return Response({
                    'success': True,
                    'message': 'If an account exists with this email, a reset link will be sent'
                }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """Confirm password reset with OTP and set new password"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            new_password = serializer.validated_data['new_password']

            try:
                account = Account.objects.get(email=email)

                # Verify OTP
                if not account.activation_code:
                    return Response({
                        'success': False,
                        'message': 'No OTP found. Please request a new reset.'
                    }, status=status.HTTP_400_BAD_REQUEST)

                if account.activation_code != otp:
                    return Response({
                        'success': False,
                        'message': 'Invalid OTP'
                    }, status=status.HTTP_400_BAD_REQUEST)

                if timezone.now() > account.activation_code_expires_at:
                    return Response({
                        'success': False,
                        'message': 'OTP has expired. Please request a new one.'
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Reset password
                account.set_password(new_password)
                account.activation_code = None  # Clear OTP after use
                account.save(update_fields=['password', 'activation_code'])

                # Send password changed notification in background thread
                thread = threading.Thread(
                    target=EmailService.send_password_changed_email,
                    args=(email, account.first_name)
                )
                thread.daemon = True
                thread.start()

                return Response({
                    'success': True,
                    'message': 'Password reset successful. You can now login with your new password.'
                }, status=status.HTTP_200_OK)

            except Account.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Account not found'
                }, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordChangeView(APIView):
    """Change password for authenticated users"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            user = request.user
            new_password = serializer.validated_data['new_password']

            # Update password
            user.set_password(new_password)
            user.save(update_fields=['password'])

            # Keep user logged in after password change
            update_session_auth_hash(request, user)

            # Send notification email in background thread
            thread = threading.Thread(
                target=EmailService.send_password_changed_email,
                args=(user.email, user.first_name)
            )
            thread.daemon = True
            thread.start()

            return Response({
                'success': True,
                'message': 'Password changed successfully'
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """Logout user by blacklisting refresh token"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from rest_framework_simplejwt.tokens import RefreshToken

        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()

            return Response({
                'success': True,
                'message': 'Successfully logged out'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)