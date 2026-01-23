# accounts/utils/email_service.py
import logging
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class EmailService:
    @staticmethod
    def send_otp_email(to_email, otp, purpose='verification'):
        """
        Send OTP email for verification or password reset
        
        Args:
            to_email: Recipient email address
            otp: The OTP code
            purpose: 'verification' or 'password_reset'
        """
        subject_map = {
            'verification': _('Verify Your Email Address'),
            'password_reset': _('Reset Your Password'),
        }
        
        template_map = {
            'verification': 'accounts/email/verification_otp.html',
            'password_reset': 'accounts/email/password_reset_otp.html',
        }
        
        subject = subject_map.get(purpose, _('Your OTP Code'))
        template = template_map.get(purpose, 'accounts/email/generic_otp.html')
        
        try:
            context = {
                'otp': otp,
                'email': to_email,
                'purpose': purpose,
                'app_name': getattr(settings, 'APP_NAME', 'Claverica'),
                'expiry_minutes': 10,
            }
            
            # Try to render HTML template
            html_message = render_to_string(template, context)
            plain_message = strip_tags(html_message)
            
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@claverica.com')
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=from_email,
                recipient_list=[to_email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"OTP email sent to {to_email} for {purpose}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send OTP email to {to_email}: {e}")
            return False
    
    @staticmethod
    def send_welcome_email(to_email, first_name):
        """Send welcome email after successful registration"""
        try:
            subject = _('Welcome to Claverica!')
            template = 'accounts/email/welcome.html'
            
            context = {
                'first_name': first_name,
                'email': to_email,
                'app_name': getattr(settings, 'APP_NAME', 'Claverica'),
            }
            
            html_message = render_to_string(template, context)
            plain_message = strip_tags(html_message)
            
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@claverica.com')
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=from_email,
                recipient_list=[to_email],
                html_message=html_message,
                fail_silently=True,  # Don't fail registration if welcome email fails
            )
            
            logger.info(f"Welcome email sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send welcome email to {to_email}: {e}")
            return False
    
    @staticmethod
    def send_password_changed_email(to_email, first_name):
        """Send notification when password is changed"""
        try:
            subject = _('Your Password Has Been Changed')
            template = 'accounts/email/password_changed.html'
            
            context = {
                'first_name': first_name,
                'app_name': getattr(settings, 'APP_NAME', 'Claverica'),
            }
            
            html_message = render_to_string(template, context)
            plain_message = strip_tags(html_message)
            
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@claverica.com')
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=from_email,
                recipient_list=[to_email],
                html_message=html_message,
                fail_silently=True,
            )
            
            logger.info(f"Password changed email sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send password changed email to {to_email}: {e}")
            return False