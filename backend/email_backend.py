import logging
import sendgrid
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings

logger = logging.getLogger(__name__)

class SendGridEmailBackend(BaseEmailBackend):
    """SendGrid email backend using the working API syntax"""
    
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently)
        self.api_key = settings.SENDGRID_API_KEY
        
    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        
        sent_count = 0
        for message in email_messages:
            if self._send(message):
                sent_count += 1
        return sent_count
    
    def _send(self, message):
        try:
            # Create client
            sg = sendgrid.SendGridAPIClient(api_key=self.api_key)
            
            # Get recipient
            to_email = message.to[0] if isinstance(message.to, (list, tuple)) else message.to
            
            # Build email data using the working format
            data = {
                "personalizations": [
                    {
                        "to": [{"email": to_email}]
                    }
                ],
                "from": {"email": message.from_email or settings.DEFAULT_FROM_EMAIL},
                "subject": message.subject,
                "content": [
                    {
                        "type": "text/html" if message.content_subtype == 'html' else "text/plain",
                        "value": message.body
                    }
                ]
            }
            
            # Send
            response = sg.client.mail.send.post(request_body=data)
            
            if response.status_code == 202:
                logger.info(f"✅ Email sent to {to_email}")
                return True
            else:
                logger.error(f"❌ SendGrid error: {response.status_code}")
                logger.error(f"Response: {response.body}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Email error: {e}")
            if not self.fail_silently:
                raise
            return False