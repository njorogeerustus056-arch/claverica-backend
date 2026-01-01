from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone


def send_html_email(to_email, subject, html_content):
    """Send HTML email using Django email backend"""
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body='Please view this email in HTML format.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_tac_email(to_email, tac_code, user_name="User"):
    """Send TAC code via email"""
    subject = "Your Transfer Authorization Code (TAC)"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .tac-code {{ background: white; border: 2px dashed #667eea; padding: 20px; text-align: center; border-radius: 10px; margin: 20px 0; }}
            .tac-code h2 {{ margin: 0; font-size: 36px; letter-spacing: 8px; color: #667eea; }}
            .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Transfer Authorization Code</h1>
                <p>Claverica Foreign Exchange</p>
            </div>
            <div class="content">
                <p>Hello {user_name},</p>
                <p>Your Transfer Authorization Code (TAC) has been generated. Please use this code to complete your transaction.</p>
                
                <div class="tac-code">
                    <p style="margin: 0; color: #666; font-size: 14px;">Your TAC Code:</p>
                    <h2>{tac_code}</h2>
                    <p style="margin: 0; color: #666; font-size: 12px;">Valid for 5 minutes</p>
                </div>
                
                <div class="warning">
                    <strong>⚠️ Security Notice:</strong>
                    <ul style="margin: 10px 0 0 0; padding-left: 20px;">
                        <li>This code expires in 5 minutes</li>
                        <li>Never share this code with anyone</li>
                        <li>Our staff will never ask for this code</li>
                        <li>If you didn't request this, contact us immediately</li>
                    </ul>
                </div>
                
                <p>If you have any questions, please contact our support team.</p>
                <p>Best regards,<br><strong>Claverica Team</strong></p>
            </div>
            <div class="footer">
                <p>This is an automated message, please do not reply to this email.</p>
                <p>&copy; 2025 Claverica Foreign Exchange. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_html_email(to_email, subject, html_content)


def send_kyc_submitted_email(to_email, user_name, verification_id):
    """Send KYC submission confirmation email"""
    subject = "KYC Verification Submitted Successfully"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .status-box {{ background: white; border-left: 4px solid #28a745; padding: 20px; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>✅ KYC Verification Submitted</h1>
                <p>Claverica Foreign Exchange</p>
            </div>
            <div class="content">
                <p>Hello {user_name},</p>
                <p>Thank you for submitting your KYC verification documents. We have received your application and our team is reviewing it.</p>
                
                <div class="status-box">
                    <h3 style="margin-top: 0;">Verification Details:</h3>
                    <p><strong>Verification ID:</strong> {verification_id}</p>
                    <p><strong>Status:</strong> Pending Review</p>
                    <p><strong>Expected Processing Time:</strong> 24-48 hours</p>
                </div>
                
                <p><strong>What happens next?</strong></p>
                <ol>
                    <li>Our compliance team will review your documents</li>
                    <li>You'll receive an email notification once approved</li>
                    <li>You can then access full platform features</li>
                </ol>
                
                <p>If additional information is needed, we'll contact you at this email address.</p>
                
                <p>Best regards,<br><strong>Claverica Compliance Team</strong></p>
            </div>
            <div class="footer">
                <p>&copy; 2025 Claverica Foreign Exchange. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_html_email(to_email, subject, html_content)


def send_kyc_approved_email(to_email, user_name, compliance_level):
    """Send KYC approval email"""
    subject = "🎉 KYC Verification Approved"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .success-box {{ background: white; border-left: 4px solid #28a745; padding: 20px; border-radius: 5px; margin: 20px 0; }}
            .feature-list {{ background: white; padding: 20px; border-radius: 10px; margin: 20px 0; }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎉 Verification Approved!</h1>
                <p>Claverica Foreign Exchange</p>
            </div>
            <div class="content">
                <p>Hello {user_name},</p>
                <p>Great news! Your KYC verification has been approved. You now have full access to all Claverica platform features.</p>
                
                <div class="success-box">
                    <h3 style="margin-top: 0;">✅ Verification Status</h3>
                    <p><strong>Status:</strong> Approved</p>
                    <p><strong>Compliance Level:</strong> {compliance_level.upper()}</p>
                    <p><strong>Approved Date:</strong> {timezone.now().strftime('%B %d, %Y')}</p>
                </div>
                
                <div class="feature-list">
                    <h3>You can now:</h3>
                    <ul>
                        <li>✅ Make unlimited transfers</li>
                        <li>✅ Withdraw funds to your bank account</li>
                        <li>✅ Access premium features</li>
                        <li>✅ Enjoy higher transaction limits</li>
                    </ul>
                </div>
                
                <p>Start exploring all the features available to you!</p>
                
                <p>Best regards,<br><strong>Claverica Team</strong></p>
            </div>
            <div class="footer">
                <p>&copy; 2025 Claverica Foreign Exchange. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_html_email(to_email, subject, html_content)


def send_withdrawal_confirmation_email(to_email, user_name, amount, currency):
    """Send withdrawal confirmation email"""
    subject = "Withdrawal Request Confirmed"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .amount-box {{ background: white; border: 2px solid #667eea; padding: 30px; text-align: center; border-radius: 10px; margin: 20px 0; }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>💰 Withdrawal Confirmed</h1>
                <p>Claverica Foreign Exchange</p>
            </div>
            <div class="content">
                <p>Hello {user_name},</p>
                <p>Your withdrawal request has been confirmed and is being processed.</p>
                
                <div class="amount-box">
                    <h2 style="margin: 0; color: #667eea; font-size: 48px;">{currency} {amount:,.2f}</h2>
                    <p style="margin: 10px 0 0 0; color: #666;">Withdrawal Amount</p>
                </div>
                
                <p><strong>Processing Timeline:</strong></p>
                <ul>
                    <li>Bank transfers: 1-3 business days</li>
                    <li>Crypto transfers: 10-30 minutes</li>
                </ul>
                
                <p>You'll receive another email once the funds have been sent.</p>
                
                <p>Best regards,<br><strong>Claverica Team</strong></p>
            </div>
            <div class="footer">
                <p>&copy; 2025 Claverica Foreign Exchange. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_html_email(to_email, subject, html_content)
