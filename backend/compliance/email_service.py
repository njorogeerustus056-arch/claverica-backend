from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
import logging

# Set up logging
logger = logging.getLogger(__name__)


def send_html_email(to_email, subject, html_content):
    """Send HTML email using Django email backend"""
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body='Please view this email in HTML format.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email] if isinstance(to_email, str) else to_email
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        logger.info(f"Email sent successfully to {to_email}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Error sending email: {e}")
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
                <p>&copy; {timezone.now().year} Claverica Foreign Exchange. All rights reserved.</p>
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
                <p>&copy; {timezone.now().year} Claverica Foreign Exchange. All rights reserved.</p>
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
                <p>&copy; {timezone.now().year} Claverica Foreign Exchange. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_html_email(to_email, subject, html_content)


def send_kyc_rejected_email(to_email, user_name, verification_id, reason):
    """Send KYC rejection email"""
    subject = "KYC Verification Update - Requires Additional Information"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #dc3545 0%, #fd7e14 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .notice-box {{ background: white; border-left: 4px solid #dc3545; padding: 20px; border-radius: 5px; margin: 20px 0; }}
            .action-box {{ background: #e7f3ff; border: 1px solid #b6d4fe; padding: 20px; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⚠️ KYC Verification Update</h1>
                <p>Claverica Foreign Exchange</p>
            </div>
            <div class="content">
                <p>Hello {user_name},</p>
                <p>We've reviewed your KYC verification application and require additional information to proceed.</p>
                
                <div class="notice-box">
                    <h3 style="margin-top: 0;">Application Details:</h3>
                    <p><strong>Verification ID:</strong> {verification_id}</p>
                    <p><strong>Status:</strong> Requires Additional Information</p>
                    <p><strong>Reason:</strong> {reason}</p>
                </div>
                
                <div class="action-box">
                    <h3 style="margin-top: 0;">📋 Next Steps:</h3>
                    <ol>
                        <li>Review the reason provided above</li>
                        <li>Submit the required documents/information</li>
                        <li>Resubmit your KYC application</li>
                        <li>Our team will review within 24-48 hours</li>
                    </ol>
                </div>
                
                <p><strong>How to resubmit:</strong></p>
                <ul>
                    <li>Login to your Claverica account</li>
                    <li>Go to Profile → KYC Verification</li>
                    <li>Upload the required documents</li>
                    <li>Submit for review</li>
                </ul>
                
                <p>If you have questions about the requirements, please contact our support team.</p>
                
                <p>Best regards,<br><strong>Claverica Compliance Team</strong></p>
            </div>
            <div class="footer">
                <p>&copy; {timezone.now().year} Claverica Foreign Exchange. All rights reserved.</p>
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
                <p>&copy; {timezone.now().year} Claverica Foreign Exchange. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_html_email(to_email, subject, html_content)


def send_document_verified_email(to_email, user_name, document_type, status, notes=""):
    """Send document verification email"""
    subject = f"Document Verification - {document_type}"
    
    status_display = "Approved" if status == "approved" else "Rejected"
    status_color = "#28a745" if status == "approved" else "#dc3545"
    status_icon = "✅" if status == "approved" else "❌"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, {status_color} 0%, #20c997 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .status-box {{ background: white; border-left: 4px solid {status_color}; padding: 20px; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{status_icon} Document Verification</h1>
                <p>Claverica Foreign Exchange</p>
            </div>
            <div class="content">
                <p>Hello {user_name},</p>
                <p>Your document has been reviewed by our compliance team.</p>
                
                <div class="status-box">
                    <h3 style="margin-top: 0;">Verification Result</h3>
                    <p><strong>Document Type:</strong> {document_type}</p>
                    <p><strong>Status:</strong> <span style="color: {status_color}; font-weight: bold;">{status_display}</span></p>
                    <p><strong>Verified Date:</strong> {timezone.now().strftime('%B %d, %Y %H:%M')}</p>
                    {f'<p><strong>Notes:</strong> {notes}</p>' if notes else ''}
                </div>
                
                <p><strong>Next Steps:</strong></p>
                {"<p>Your document has been approved and will be used for your KYC verification.</p>" if status == "approved" else "<p>Please submit a new document following our guidelines. You can find the requirements in your KYC verification section.</p>"}
                
                <p>If you have any questions, please contact our support team.</p>
                
                <p>Best regards,<br><strong>Claverica Compliance Team</strong></p>
            </div>
            <div class="footer">
                <p>&copy; {timezone.now().year} Claverica Foreign Exchange. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_html_email(to_email, subject, html_content)


def send_transaction_receipt_email(to_email, user_name, transaction_id, amount, currency, transaction_type):
    """Send transaction receipt email"""
    subject = f"Transaction Receipt - {transaction_id}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #6c757d 0%, #495057 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .receipt-box {{ background: white; border: 2px solid #dee2e6; padding: 30px; border-radius: 10px; margin: 20px 0; }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📄 Transaction Receipt</h1>
                <p>Claverica Foreign Exchange</p>
            </div>
            <div class="content">
                <p>Hello {user_name},</p>
                <p>Your transaction has been completed successfully. Here's your receipt:</p>
                
                <div class="receipt-box">
                    <h3 style="margin-top: 0; border-bottom: 2px solid #f8f9fa; padding-bottom: 10px;">Transaction Details</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;"><strong>Transaction ID:</strong></td>
                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">{transaction_id}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;"><strong>Type:</strong></td>
                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">{transaction_type}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;"><strong>Amount:</strong></td>
                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right; font-weight: bold; font-size: 18px;">{currency} {amount:,.2f}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;"><strong>Date:</strong></td>
                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">{timezone.now().strftime('%B %d, %Y %H:%M')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;"><strong>Status:</strong></td>
                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right; color: #28a745; font-weight: bold;">Completed</td>
                        </tr>
                    </table>
                </div>
                
                <p>This receipt confirms that your transaction has been processed successfully. Please keep this for your records.</p>
                
                <p>If you have any questions about this transaction, please contact our support team.</p>
                
                <p>Best regards,<br><strong>Claverica Team</strong></p>
            </div>
            <div class="footer">
                <p>&copy; {timezone.now().year} Claverica Foreign Exchange. All rights reserved.</p>
                <p>This is an automated message. Please do not reply to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_html_email(to_email, subject, html_content)


def send_security_alert_email(to_email, user_name, alert_type, alert_details, location=None):
    """Send security alert email"""
    subject = f"Security Alert: {alert_type}"
    
    timestamp = timezone.now().strftime('%B %d, %Y %H:%M:%S')
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #dc3545 0%, #fd7e14 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .alert-box {{ background: white; border-left: 4px solid #dc3545; padding: 20px; border-radius: 5px; margin: 20px 0; }}
            .action-box {{ background: #e7f3ff; border: 1px solid #b6d4fe; padding: 20px; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⚠️ Security Alert</h1>
                <p>Claverica Foreign Exchange</p>
            </div>
            <div class="content">
                <p>Hello {user_name},</p>
                <p>We detected a security event on your account that requires your attention.</p>
                
                <div class="alert-box">
                    <h3 style="margin-top: 0;">Security Event Details</h3>
                    <p><strong>Alert Type:</strong> {alert_type}</p>
                    <p><strong>Details:</strong> {alert_details}</p>
                    <p><strong>Time:</strong> {timestamp}</p>
                    {f'<p><strong>Location:</strong> {location}</p>' if location else ''}
                </div>
                
                <div class="action-box">
                    <h3 style="margin-top: 0;">Recommended Actions</h3>
                    <ul>
                        <li>If this was you, no action is required</li>
                        <li>If you don't recognize this activity, change your password immediately</li>
                        <li>Enable two-factor authentication if not already enabled</li>
                        <li>Review your recent account activity</li>
                    </ul>
                </div>
                
                <p><strong>If you suspect unauthorized access:</strong></p>
                <ol>
                    <li>Change your password immediately</li>
                    <li>Enable two-factor authentication</li>
                    <li>Contact our support team at support@claverica.com</li>
                </ol>
                
                <p>For your security, this email cannot be replied to.</p>
                
                <p>Best regards,<br><strong>Claverica Security Team</strong></p>
            </div>
            <div class="footer">
                <p>&copy; {timezone.now().year} Claverica Foreign Exchange. All rights reserved.</p>
                <p>This is an automated security alert. Please do not reply to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_html_email(to_email, subject, html_content)


def send_video_call_scheduled_email(to_email, user_name, scheduled_time, meeting_id, meeting_password=None):
    """Send video call scheduled email"""
    subject = "Video Call Scheduled for KYC Verification"
    
    formatted_time = scheduled_time.strftime('%B %d, %Y at %I:%M %p %Z')
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #007bff 0%, #6610f2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .meeting-box {{ background: white; border: 2px solid #007bff; padding: 30px; border-radius: 10px; margin: 20px 0; }}
            .instructions {{ background: #e7f3ff; border-left: 4px solid #007bff; padding: 20px; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎥 Video Call Scheduled</h1>
                <p>Claverica Foreign Exchange - KYC Verification</p>
            </div>
            <div class="content">
                <p>Hello {user_name},</p>
                <p>Your video call for KYC verification has been scheduled. Please join the call at the scheduled time.</p>
                
                <div class="meeting-box">
                    <h3 style="margin-top: 0; border-bottom: 2px solid #f8f9fa; padding-bottom: 10px;">Meeting Details</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;"><strong>Scheduled Time:</strong></td>
                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right; font-weight: bold;">{formatted_time}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;"><strong>Meeting ID:</strong></td>
                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">{meeting_id}</td>
                        </tr>
                        {f'<tr><td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;"><strong>Password:</strong></td><td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">{meeting_password}</td></tr>' if meeting_password else ''}
                        <tr>
                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;"><strong>Purpose:</strong></td>
                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">KYC Verification</td>
                        </tr>
                    </table>
                </div>
                
                <div class="instructions">
                    <h3 style="margin-top: 0;">📋 How to Join:</h3>
                    <ol>
                        <li>Click the meeting link or join with the meeting ID above</li>
                        <li>Join 5 minutes before the scheduled time</li>
                        <li>Have your government-issued ID ready</li>
                        <li>Ensure you have good lighting and a stable internet connection</li>
                    </ol>
                </div>
                
                <p><strong>Required Documents:</strong></p>
                <ul>
                    <li>Government-issued photo ID (Passport, Driver's License, National ID)</li>
                    <li>Proof of address (Utility bill, Bank statement)</li>
                </ul>
                
                <p>If you need to reschedule or have questions, please contact our support team.</p>
                
                <p>Best regards,<br><strong>Claverica Compliance Team</strong></p>
            </div>
            <div class="footer">
                <p>&copy; {timezone.now().year} Claverica Foreign Exchange. All rights reserved.</p>
                <p>This is an automated message. Please do not reply to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_html_email(to_email, subject, html_content)


def send_video_call_reminder_email(to_email, user_name, scheduled_time, meeting_id, meeting_password=None):
    """Send video call reminder email"""
    subject = "Reminder: Upcoming KYC Video Call"
    
    formatted_time = scheduled_time.strftime('%B %d, %Y at %I:%M %p %Z')
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #fd7e14 0%, #ffc107 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .reminder-box {{ background: white; border: 2px solid #fd7e14; padding: 30px; border-radius: 10px; margin: 20px 0; }}
            .instructions {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 20px; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⏰ Video Call Reminder</h1>
                <p>Claverica Foreign Exchange - KYC Verification</p>
            </div>
            <div class="content">
                <p>Hello {user_name},</p>
                <p>This is a reminder for your upcoming KYC verification video call.</p>
                
                <div class="reminder-box">
                    <h3 style="margin-top: 0; border-bottom: 2px solid #f8f9fa; padding-bottom: 10px;">Meeting Details</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;"><strong>Scheduled Time:</strong></td>
                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right; font-weight: bold; color: #fd7e14;">{formatted_time}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;"><strong>Meeting ID:</strong></td>
                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">{meeting_id}</td>
                        </tr>
                        {f'<tr><td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;"><strong>Password:</strong></td><td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">{meeting_password}</td></tr>' if meeting_password else ''}
                        <tr>
                            <td style="padding: 8px 0;"><strong>Time Until Call:</strong></td>
                            <td style="padding: 8px 0; text-align: right; font-weight: bold;">1 hour</td>
                        </tr>
                    </table>
                </div>
                
                <div class="instructions">
                    <h3 style="margin-top: 0;">📋 Preparation Checklist:</h3>
                    <ul>
                        <li>✅ Test your camera and microphone</li>
                        <li>✅ Ensure good lighting in your room</li>
                        <li>✅ Have your ID documents ready</li>
                        <li>✅ Join 5 minutes before the scheduled time</li>
                        <li>✅ Use a stable internet connection</li>
                    </ul>
                </div>
                
                <p><strong>Required Documents:</strong></p>
                <ul>
                    <li>Government-issued photo ID (Passport, Driver's License, National ID)</li>
                    <li>Proof of address (Utility bill, Bank statement)</li>
                </ul>
                
                <p>If you need to reschedule, please contact our support team immediately.</p>
                
                <p>Best regards,<br><strong>Claverica Compliance Team</strong></p>
            </div>
            <div class="footer">
                <p>&copy; {timezone.now().year} Claverica Foreign Exchange. All rights reserved.</p>
                <p>This is an automated reminder. Please do not reply to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_html_email(to_email, subject, html_content)


def send_video_call_completed_email(to_email, user_name, verification_status, notes=""):
    """Send video call completed email"""
    subject = "KYC Video Call Completed"
    
    status_display = "Successful" if verification_status else "Requires Follow-up"
    status_color = "#28a745" if verification_status else "#dc3545"
    status_icon = "✅" if verification_status else "⚠️"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, {status_color} 0%, #20c997 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .status-box {{ background: white; border-left: 4px solid {status_color}; padding: 20px; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{status_icon} Video Call Completed</h1>
                <p>Claverica Foreign Exchange - KYC Verification</p>
            </div>
            <div class="content">
                <p>Hello {user_name},</p>
                <p>Your KYC verification video call has been completed.</p>
                
                <div class="status-box">
                    <h3 style="margin-top: 0;">Verification Result</h3>
                    <p><strong>Status:</strong> <span style="color: {status_color}; font-weight: bold;">{status_display}</span></p>
                    <p><strong>Completed Date:</strong> {timezone.now().strftime('%B %d, %Y %H:%M')}</p>
                    {f'<p><strong>Notes:</strong> {notes}</p>' if notes else ''}
                </div>
                
                {"<p>✅ Your video verification was successful. Our compliance team will now review the information and you will receive a final KYC verification status within 24-48 hours.</p>" if verification_status else "<p>⚠️ Additional information or clarification is required. Our compliance team will contact you with the next steps or you may need to schedule another call.</p>"}
                
                <p><strong>Next Steps:</strong></p>
                {"<ul><li>Wait for final KYC verification email</li><li>You will receive full platform access upon approval</li><li>Check your email regularly for updates</li></ul>" if verification_status else "<ul><li>Our team will contact you with specific requirements</li><li>You may need to submit additional documents</li><li>Follow the instructions provided by our team</li></ul>"}
                
                <p>If you have any questions, please contact our support team.</p>
                
                <p>Best regards,<br><strong>Claverica Compliance Team</strong></p>
            </div>
            <div class="footer">
                <p>&copy; {timezone.now().year} Claverica Foreign Exchange. All rights reserved.</p>
                <p>This is an automated message. Please do not reply to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_html_email(to_email, subject, html_content)


def send_compliance_decision_email(to_email, user_name, request_id, decision, reason=""):
    """Send email for compliance decision (approval/rejection)"""
    from datetime import datetime
    
    subject = f"Compliance Request {decision.title()}"
    
    if decision.lower() == 'approved':
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #28a745;">✅ Compliance Request Approved</h2>
            <p>Hello {user_name},</p>
            <p>Your compliance request <strong>#{request_id}</strong> has been <strong>approved</strong>.</p>
            <p>You can now proceed with your transactions.</p>
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p><strong>Request ID:</strong> {request_id}</p>
                <p><strong>Status:</strong> Approved ✅</p>
                <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            <p>If you have any questions, please contact our support team.</p>
            <p>Best regards,<br>The Compliance Team</p>
        </div>
        """
    else:
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #dc3545;">❌ Compliance Request Rejected</h2>
            <p>Hello {user_name},</p>
            <p>Your compliance request <strong>#{request_id}</strong> has been <strong>rejected</strong>.</p>
            <p><strong>Reason:</strong> {reason if reason else 'Please check your submission and try again.'}</p>
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p><strong>Request ID:</strong> {request_id}</p>
                <p><strong>Status:</strong> Rejected ❌</p>
                <p><strong>Reason:</strong> {reason if reason else 'Not specified'}</p>
                <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            <p>Please review your submission and submit again with corrected information.</p>
            <p>If you have any questions, please contact our support team.</p>
            <p>Best regards,<br>The Compliance Team</p>
        </div>
        """
    
    return send_html_email(to_email, subject, html_content)


def send_compliance_escalation_email(to_email, user_name, request_id, escalated_to, escalation_reason=""):
    """Send compliance escalation notification email"""
    subject = f"⚠️ Compliance Request {request_id} Escalated"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #fd7e14 0%, #dc3545 100%);
                color: white;
                padding: 30px;
                text-align: center;
                border-radius: 10px 10px 0 0;
            }}
            .content {{
                background: #f9f9f9;
                padding: 30px;
                border-radius: 0 0 10px 10px;
            }}
            .escalation-box {{
                background: white;
                border-left: 4px solid #fd7e14;
                padding: 20px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .next-steps {{
                background: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 20px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .footer {{
                text-align: center;
                padding: 20px;
                color: #666;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⚠️ Compliance Request Escalated</h1>
                <p>Claverica Foreign Exchange</p>
            </div>
            <div class="content">
                <p>Hello {user_name},</p>
                <p>Your compliance request requires additional review and has been escalated to a senior compliance officer.</p>
                
                <div class="escalation-box">
                    <h3 style="margin-top: 0;">Escalation Details</h3>
                    <p><strong>Request ID:</strong> {request_id}</p>
                    <p><strong>Escalated To:</strong> {escalated_to}</p>
                    <p><strong>Date Escalated:</strong> {timezone.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                    {f'<p><strong>Reason for Escalation:</strong> {escalation_reason}</p>' if escalation_reason else '<p><strong>Reason for Escalation:</strong> Additional review required</p>'}
                </div>
                
                <div class="next-steps">
                    <h3 style="margin-top: 0;">📋 What Happens Next?</h3>
                    <ol>
                        <li>A senior compliance officer will review your request</li>
                        <li>You may be contacted for additional information</li>
                        <li>You will receive a final decision within 48 hours</li>
                        <li>Check your email regularly for updates</li>
                    </ol>
                </div>
                
                <p><strong>No action required from you at this time.</strong> Our team is working to resolve this as quickly as possible.</p>
                
                <p>If you have any questions, please contact our support team.</p>
                
                <p>Best regards,<br><strong>Claverica Compliance Team</strong></p>
            </div>
            <div class="footer">
                <p>&copy; {timezone.now().year} Claverica Foreign Exchange. All rights reserved.</p>
                <p>This is an automated notification. Please do not reply to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_html_email(to_email, subject, html_content)
def send_kyc_approval_email(email, name, compliance_level):
    """Send KYC approval email"""
    print(f"Sending KYC approval email to {email}")
    # TODO: Implement actual email sending
    return True

def send_kyc_rejection_email(email, name, kyc_id, reason):
    """Send KYC rejection email"""
    print(f"Sending KYC rejection email to {email}")
    # TODO: Implement actual email sending
    return True

def send_tac_code_email(email, tac_code, purpose):
    """Send TAC code email"""
    print(f"Sending TAC code {tac_code} to {email} for {purpose}")
    # TODO: Implement actual email sending
    return True
