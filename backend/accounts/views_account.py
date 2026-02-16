import logging
import threading
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth import update_session_auth_hash
from django.utils.crypto import get_random_string
from django.core.cache import cache

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

# ========== REGISTRATION & ACTIVATION VIEWS ==========

class RegisterView(APIView):
    """Register new account and send activation code"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AccountRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            account = serializer.save()

            # Send activation email in background thread
            thread = threading.Thread(
                target=self.send_activation_email,
                args=(account.email, account.activation_code, account.first_name)
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

    def send_activation_email(self, email, activation_code, first_name):
        """Send activation code email using HTML template"""
        subject = f'Activate Your Account - {settings.APP_NAME}'

        # Context for template
        context = {
            'app_name': settings.APP_NAME,
            'activation_code': activation_code,
            'first_name': first_name,
            'activation_url': f"{getattr(settings, 'FRONTEND_URL', '')}/activate",
            'expiry_hours': 24
        }

        # Render HTML template
        html_message = render_to_string('accounts/email/verification_otp.html', context)

        # Plain text fallback - FIXED: Changed APP_name to APP_NAME on line 86
        plain_message = f"""
Hello {first_name},

Thank you for registering with {settings.APP_NAME}!

Your activation code is: {activation_code}

Enter this code on our website to activate your account.
This code expires in 24 hours.

If you didn't create an account, please ignore this email.

Best regards,
The {settings.APP_NAME} Team
"""

        try:
            # Create email with both HTML and plain text versions
            email_msg = EmailMultiAlternatives(
                subject,
                plain_message.strip(),
                settings.DEFAULT_FROM_EMAIL,
                [email]
            )
            email_msg.attach_alternative(html_message, "text/html")
            email_msg.send(fail_silently=False)
            logger.info(f"Activation email sent to {email}")
        except Exception as e:
            logger.error(f"Email sending FAILED for {email}: {e}")


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
                # CRITICAL: Generate account number if not exists
                if not account.account_number:
                    account.account_number = Account.objects.generate_account_number(account)
                    account.save(update_fields=['account_number'])
                    logger.info(f"Account number generated for {account.email}: {account.account_number}")

                # Send welcome email with account number in background thread
                thread = threading.Thread(
                    target=self.send_welcome_email,
                    args=(account,)
                )
                thread.daemon = True
                thread.start()

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
                        'phone': account.phone,
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

    def send_welcome_email(self, account):
        """Send welcome email with account number after activation"""
        subject = f'Welcome to {settings.APP_NAME} - Your Account is Ready!'

        # Format registration date
        registration_date = account.created_at.strftime('%B %d, %Y')

        # Context for template
        context = {
            'app_name': settings.APP_NAME,
            'first_name': account.first_name,
            'last_name': account.last_name,
            'email': account.email,
            'phone': account.phone,
            'account_number': account.account_number,
            'registration_date': registration_date,
            'dashboard_url': f"{getattr(settings, 'FRONTEND_URL', '')}/dashboard",
            'profile_url': f"{getattr(settings, 'FRONTEND_URL', '')}/profile"
        }

        # Render HTML template
        html_message = render_to_string('accounts/email/welcome.html', context)

        # Plain text fallback
        plain_message = f"""
Welcome to {settings.APP_NAME}!

Dear {account.first_name},

Congratulations! Your account has been successfully activated.

Your unique account number is: {account.account_number}

Please save this number as you will need it for all transactions and identification.

You can now:
- View your wallet balance
- Make transfers
- Complete your KYC verification
- Access card services

Thank you for choosing {settings.APP_NAME}.

Best regards,
The {settings.APP_NAME} Team
"""

        try:
            email_msg = EmailMultiAlternatives(
                subject,
                plain_message.strip(),
                settings.DEFAULT_FROM_EMAIL,
                [account.email]
            )
            email_msg.attach_alternative(html_message, "text/html")
            email_msg.send(fail_silently=False)
            logger.info(f"Welcome email sent to {account.email} with account number {account.account_number}")
        except Exception as e:
            logger.error(f"Welcome email FAILED for {account.email}: {e}")


class ResendActivationView(APIView):
    """Resend activation code"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResendActivationSerializer(data=request.data)
        if serializer.is_valid():
            account = serializer.validated_data['email']  # This returns account object

            # Generate new activation code
            new_code = account.generate_activation_code()

            # Send new activation email in background thread
            thread = threading.Thread(
                target=self.send_activation_email,
                args=(account.email, new_code, account.first_name)
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

    def send_activation_email(self, email, activation_code, first_name):
        """Send activation code email using HTML template (resend)"""
        subject = f'New Activation Code - {settings.APP_NAME}'

        # Context for template
        context = {
            'app_name': settings.APP_NAME,
            'activation_code': activation_code,
            'first_name': first_name,
            'activation_url': f"{getattr(settings, 'FRONTEND_URL', '')}/activate",
            'expiry_hours': 24
        }

        # Render HTML template
        html_message = render_to_string('accounts/email/verification_otp.html', context)

        # Plain text fallback
        plain_message = f"""
Hello {first_name},

You requested a new activation code for {settings.APP_NAME}.

Your new activation code is: {activation_code}

Enter this code on our website to activate your account.
This code expires in 24 hours.

Best regards,
The {settings.APP_NAME} Team
"""

        try:
            email_msg = EmailMultiAlternatives(
                subject,
                plain_message.strip(),
                settings.DEFAULT_FROM_EMAIL,
                [email]
            )
            email_msg.attach_alternative(html_message, "text/html")
            email_msg.send(fail_silently=False)
            logger.info(f"Resent activation email to {email}")
        except Exception as e:
            logger.error(f"Email resend FAILED for {email}: {e}")


# ========== LOGIN VIEW ==========

class LoginView(APIView):
    """Login with email and password with rate limiting"""
    permission_classes = [AllowAny]

    def post(self, request):
        from rest_framework_simplejwt.tokens import RefreshToken

        # Rate limiting by IP
        ip = request.META.get('REMOTE_ADDR', '')
        cache_key = f'login_attempts_{ip}'
        attempts = cache.get(cache_key, 0)

        if attempts >= 5:  # Max 5 attempts per 15 minutes
            logger.warning(f"Rate limit exceeded for IP: {ip}")
            return Response({
                'success': False,
                'message': 'Too many login attempts. Please try again later.'
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)

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
                # Increment failed attempts
                cache.set(cache_key, attempts + 1, 900)  # 15 minutes
                logger.info(f"Failed login attempt for {email} from IP {ip}")
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

            # Clear rate limit on success
            cache.delete(cache_key)

            # Generate JWT tokens
            refresh = RefreshToken.for_user(account)

            logger.info(f"Successful login for {email} from IP {ip}")

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
            # Increment failed attempts even for non-existent emails
            cache.set(cache_key, attempts + 1, 900)
            logger.info(f"Login attempt for non-existent email {email} from IP {ip}")
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


# ========== PASSWORD MANAGEMENT VIEWS ==========

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
                    target=self.send_password_reset_email,
                    args=(email, reset_otp, account.first_name)
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

    def send_password_reset_email(self, email, otp, first_name):
        """Send password reset email with OTP"""
        subject = f'Password Reset - {settings.APP_NAME}'

        context = {
            'app_name': settings.APP_NAME,
            'otp': otp,
            'first_name': first_name,
            'expiry_minutes': 10
        }

        html_message = render_to_string('accounts/email/password_reset_otp.html', context)

        plain_message = f"""
Hello {first_name},

You requested to reset your password.

Your OTP code is: {otp}

This code expires in 10 minutes.

If you didn't request this, please ignore this email.

Best regards,
The {settings.APP_NAME} Team
"""

        try:
            email_msg = EmailMultiAlternatives(
                subject,
                plain_message.strip(),
                settings.DEFAULT_FROM_EMAIL,
                [email]
            )
            email_msg.attach_alternative(html_message, "text/html")
            email_msg.send(fail_silently=False)
            logger.info(f"Password reset email sent to {email}")
        except Exception as e:
            logger.error(f"Password reset email FAILED for {email}: {e}")


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
                account.activation_code = None
                account.save(update_fields=['password', 'activation_code'])

                # Send password changed notification
                thread = threading.Thread(
                    target=self.send_password_changed_email,
                    args=(account.email, account.first_name)
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

    def send_password_changed_email(self, email, first_name):
        """Send password changed notification"""
        subject = f'Password Changed - {settings.APP_NAME}'

        context = {
            'app_name': settings.APP_NAME,
            'first_name': first_name
        }

        html_message = render_to_string('accounts/email/password_changed.html', context)

        plain_message = f"""
Hello {first_name},

Your password has been changed successfully.

If you did not make this change, please contact support immediately.

Best regards,
The {settings.APP_NAME} Team
"""

        try:
            email_msg = EmailMultiAlternatives(
                subject,
                plain_message.strip(),
                settings.DEFAULT_FROM_EMAIL,
                [email]
            )
            email_msg.attach_alternative(html_message, "text/html")
            email_msg.send(fail_silently=False)
            logger.info(f"Password changed email sent to {email}")
        except Exception as e:
            logger.error(f"Password changed email FAILED for {email}: {e}")


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

            # Send notification email
            thread = threading.Thread(
                target=self.send_password_changed_email,
                args=(user.email, user.first_name)
            )
            thread.daemon = True
            thread.start()

            return Response({
                'success': True,
                'message': 'Password changed successfully'
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def send_password_changed_email(self, email, first_name):
        """Send password changed notification"""
        subject = f'Password Changed - {settings.APP_NAME}'

        context = {
            'app_name': settings.APP_NAME,
            'first_name': first_name
        }

        html_message = render_to_string('accounts/email/password_changed.html', context)

        plain_message = f"""
Hello {first_name},

Your password has been changed successfully.

If you did not make this change, please contact support immediately.

Best regards,
The {settings.APP_NAME} Team
"""

        try:
            email_msg = EmailMultiAlternatives(
                subject,
                plain_message.strip(),
                settings.DEFAULT_FROM_EMAIL,
                [email]
            )
            email_msg.attach_alternative(html_message, "text/html")
            email_msg.send(fail_silently=False)
            logger.info(f"Password changed email sent to {email}")
        except Exception as e:
            logger.error(f"Password changed email FAILED for {email}: {e}")


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