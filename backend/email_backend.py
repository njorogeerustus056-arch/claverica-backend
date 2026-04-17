import logging
import os
import sendgrid
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings

logger = logging.getLogger(__name__)

class SendGridEmailBackend(BaseEmailBackend):
    """SendGrid email backend that properly sends BOTH HTML and plain text versions"""
    
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently)
        # Try to get API key from environment first, then from settings
        self.api_key = os.environ.get('SENDGRID_API_KEY')
        if not self.api_key:
            self.api_key = getattr(settings, 'SENDGRID_API_KEY', None)
        
        if self.api_key:
            logger.info(f"SendGrid backend initialized. API Key present: {self.api_key[:8]}...")
        else:
            logger.error("CRITICAL: No SendGrid API key found!")
        
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
            if not self.api_key:
                logger.error("Cannot send email: No API key available")
                return False
            
            # Create client
            sg = sendgrid.SendGridAPIClient(api_key=self.api_key)
            
            # Get recipient
            to_email = message.to[0] if isinstance(message.to, (list, tuple)) else message.to
            
            # 🔥 FIX: Build content array to include BOTH plain text AND HTML
            content = []
            
            # Add plain text version (always present)
            if message.body:
                content.append({
                    "type": "text/plain",
                    "value": message.body
                })
            
            # Add HTML version if it exists in alternatives
            if hasattr(message, 'alternatives') and message.alternatives:
                for alt_content, alt_type in message.alternatives:
                    if alt_type == 'text/html':
                        content.append({
                            "type": "text/html",
                            "value": alt_content
                        })
            
            # If no content found (fallback)
            if not content:
                content.append({
                    "type": "text/plain",
                    "value": "Please view this email in HTML format for the best experience."
                })
            
            # Build email data with BOTH versions
            data = {
                "personalizations": [
                    {
                        "to": [{"email": to_email}]
                    }
                ],
                "from": {"email": message.from_email or settings.DEFAULT_FROM_EMAIL},
                "subject": message.subject,
                "content": content  # 🔥 NOW CONTAINS BOTH HTML AND PLAIN TEXT
            }
            
            # Send
            response = sg.client.mail.send.post(request_body=data)
            
            if response.status_code == 202:
                logger.info(f"✅ Email sent to {to_email} with {len(content)} content type(s)")
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