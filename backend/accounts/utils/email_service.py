# accounts/utils/email_service.py
import logging
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.template.exceptions import TemplateDoesNotExist
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class EmailService:
    @staticmethod
    def _render_email_template(template_name, context, default_text):
        """
        Safely render template or return default text if template doesn't exist
        This prevents worker timeout when templates are missing
        """
        try:
            # Try to render the HTML template
            html_message = render_to_string(template_name, context)
            plain_message = strip_tags(html_message)
            return html_message, plain_message
        except TemplateDoesNotExist:
            logger.warning(f"Template {template_name} not found, using default text")
            # Log where Django is looking for templates (helpful for debugging)
            from django.template.engine import Engine
            engine = Engine.get_default()
            template_dirs = []
            for loader in engine.template_loaders:
                if hasattr(loader, 'get_dirs'):
                    template_dirs.extend(loader.get_dirs())
            logger.info(f"Django template directories: {template_dirs}")
            
            # Return default plain text message
            return None, default_text
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {e}")
            return None, default_text

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

        default_text_map = {
            'verification': f"Your verification code is: {otp}\nThis code expires in 10 minutes.\n\nIf you didn't request this, please ignore this email.\n\nClaverica Team",
            'password_reset': f"Your password reset code is: {otp}\nThis code expires in 10 minutes.\n\nIf you didn't request this, please ignore this email.\n\nClaverica Team",
        }

        subject = subject_map.get(purpose, _('Your OTP Code'))
        template = template_map.get(purpose)
        default_text = default_text_map.get(purpose, f"Your code is: {otp}")

        context = {
            'otp': otp,
            'email': to_email,
            'purpose': purpose,
            'app_name': getattr(settings, 'APP_NAME', 'Claverica'),
            'expiry_minutes': 10,
        }

        try:
            # Render template safely
            html_message, plain_message = EmailService._render_email_template(
                template, context, default_text
            )

            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@claverica.com')

            # Only pass html_message if it exists
            email_kwargs = {
                'subject': subject,
                'message': plain_message,
                'from_email': from_email,
                'recipient_list': [to_email],
                'fail_silently': False,  # Set to False to catch errors
            }
            
            if html_message:
                email_kwargs['html_message'] = html_message

            send_mail(**email_kwargs)

            logger.info(f"OTP email sent to {to_email} for {purpose}")
            return True

        except Exception as e:
            logger.error(f"Failed to send OTP email to {to_email}: {e}")
            return False

    @staticmethod
    def send_welcome_email(to_email, first_name, last_name="", account_number="", phone="", **kwargs):
        """Send welcome email after successful registration"""
        default_text = f"""
Welcome {first_name} {last_name} to Claverica!

Your account has been successfully created.

Account Details:
- Account Number: {account_number}
- Email: {to_email}
- Phone: {phone}

Next Steps:
1. Verify your email using the OTP sent separately
2. Complete your profile setup
3. Explore our banking features

If you have any questions, please contact our support team.

Welcome aboard!
The Claverica Team
"""
        
        try:
            context = {
                'first_name': first_name,
                'last_name': last_name,
                'email': to_email,
                'phone': phone,
                'account_number': account_number,
                'app_name': getattr(settings, 'APP_NAME', 'Claverica'),
                'registration_date': kwargs.get('registration_date', ''),
                'street': kwargs.get('street', ''),
                'city': kwargs.get('city', ''),
                'state': kwargs.get('state', ''),
                'zip_code': kwargs.get('zip_code', ''),
                'occupation': kwargs.get('occupation', ''),
                'employer': kwargs.get('employer', ''),
            }

            html_message, plain_message = EmailService._render_email_template(
                'accounts/email/welcome.html',
                context,
                default_text
            )

            email_kwargs = {
                'subject': _('Welcome to Claverica!'),
                'message': plain_message,
                'from_email': getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@claverica.com'),
                'recipient_list': [to_email],
                'fail_silently': True,  # Don't fail registration if welcome email fails
            }
            
            if html_message:
                email_kwargs['html_message'] = html_message

            send_mail(**email_kwargs)
            logger.info(f"Welcome email sent to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send welcome email to {to_email}: {e}")
            return False

    @staticmethod
    def send_password_changed_email(to_email, first_name):
        """Send notification when password is changed"""
        default_text = f"""
Hello {first_name},

Your password has been successfully changed.

SECURITY NOTICE: If you didn't make this change, please contact our support team immediately.

For your security, we recommend:
- Use a unique password for your Claverica account
- Enable two-factor authentication if available
- Regularly review your account activity

The Claverica Team
"""
        
        try:
            context = {
                'first_name': first_name,
                'app_name': getattr(settings, 'APP_NAME', 'Claverica'),
                'login_url': '#',
            }

            html_message, plain_message = EmailService._render_email_template(
                'accounts/email/password_changed.html',
                context,
                default_text
            )

            email_kwargs = {
                'subject': _('Your Password Has Been Changed'),
                'message': plain_message,
                'from_email': getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@claverica.com'),
                'recipient_list': [to_email],
                'fail_silently': True,
            }
            
            if html_message:
                email_kwargs['html_message'] = html_message

            send_mail(**email_kwargs)
            logger.info(f"Password changed email sent to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send password changed email to {to_email}: {e}")
            return False
