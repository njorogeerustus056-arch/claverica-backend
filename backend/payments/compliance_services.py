# payments/compliance_services.py - UPDATED TO USE CENTRAL COMPLIANCE APP

from django.db import transaction as db_transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal
import logging
import requests
from django.conf import settings

from .models import (
    Transaction, PaymentTransactionNotification,
    ActivityFeed, AuditLog
)

logger = logging.getLogger(__name__)
User = get_user_model()


class ComplianceIntegrationService:
    """Service for integrating with central compliance app"""
    
    @staticmethod
    def _call_compliance_api(endpoint, data=None, method='POST'):
        """Make API call to compliance app"""
        try:
            # Get compliance app URL from settings
            base_url = getattr(settings, 'COMPLIANCE_API_URL', 'http://localhost:8000/compliance/api/')
            
            url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
            
            headers = {
                'Content-Type': 'application/json',
                # Add authentication headers if needed
            }
            
            if method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'GET':
                response = requests.get(url, params=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Compliance API call failed: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected error calling compliance API: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def request_manual_payment_approval(user, amount, currency='USD', description=""):
        """Request manual payment approval from compliance app"""
        try:
            with db_transaction.atomic():
                # Create transaction with pending compliance status
                transaction = Transaction.objects.create(
                    account=user.accounts.first() if user.accounts.exists() else None,
                    amount=amount,
                    currency=currency,
                    transaction_type='payment',
                    description=description,
                    status='pending_compliance',
                    requires_manual_approval=True
                )
                
                # Call compliance app to create approval request
                compliance_data = {
                    'app_name': 'payments',
                    'app_transaction_id': transaction.transaction_id,
                    'user_id': str(user.id),
                    'amount': str(amount),
                    'currency': currency,
                    'request_type': 'manual_payment',
                    'description': description,
                    'metadata': {
                        'transaction_type': 'payment',
                        'requires_tac': True,
                        'payment_method': 'manual_release'
                    }
                }
                
                # Call compliance API
                result = ComplianceIntegrationService._call_compliance_api(
                    'requests/create/',
                    compliance_data
                )
                
                if result.get('success'):
                    # Update transaction with compliance reference
                    transaction.compliance_reference = result['compliance_id']
                    transaction.save()
                    
                    # Create notification for admin
                    admin = User.objects.filter(is_staff=True).first()
                    notification = PaymentTransactionNotification.objects.create(
                        reference_code=transaction.transaction_id[:16],
                        sender=user,
                        receiver=admin,
                        notification_type='compliance_required',
                        amount=amount,
                        currency=currency,
                        full_message=f"Manual payment approval requested: ${amount} from {user.email}",
                        short_message=f"🔄 Manual payment: ${amount}",
                        emoji='🔄'
                    )
                    
                    # Activity feed
                    ActivityFeed.objects.create(
                        user=user,
                        activity_type='compliance_started',
                        reference=transaction.transaction_id,
                        amount=amount,
                        display_text=f"⏳ Manual payment requested: ${amount} (Waiting for approval)",
                        emoji='⏳',
                        color_class='text-yellow-600'
                    )
                    
                    return {
                        'success': True,
                        'transaction_id': transaction.transaction_id,
                        'compliance_id': result['compliance_id'],
                        'message': 'Payment request submitted. Waiting for compliance approval.'
                    }
                else:
                    # Rollback transaction if compliance request failed
                    transaction.delete()
                    return {
                        'success': False,
                        'error': f"Compliance request failed: {result.get('error')}"
                    }
                
        except Exception as e:
            logger.error(f"Manual payment request failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def request_kyc_verification(user, amount, currency='USD', form_data=None):
        """Request KYC verification for high-value transaction"""
        try:
            with db_transaction.atomic():
                # Create transaction
                transaction = Transaction.objects.create(
                    account=user.accounts.first() if user.accounts.exists() else None,
                    amount=amount,
                    currency=currency,
                    transaction_type='payment',
                    description='KYC Verification Required',
                    status='pending_compliance',
                    requires_manual_approval=True
                )
                
                # Call compliance app for KYC verification
                compliance_data = {
                    'app_name': 'payments',
                    'app_transaction_id': transaction.transaction_id,
                    'user_id': str(user.id),
                    'amount': str(amount),
                    'currency': currency,
                    'request_type': 'kyc_verification',
                    'description': 'KYC verification required for payment',
                    'metadata': {
                        'transaction_type': 'payment',
                        'kyc_type': 'enhanced',
                        'requires_video_call': True,
                        'form_data': form_data or {}
                    }
                }
                
                result = ComplianceIntegrationService._call_compliance_api(
                    'kyc/request/',
                    compliance_data
                )
                
                if result.get('success'):
                    transaction.compliance_reference = result['kyc_id']
                    transaction.save()
                    
                    # Notify admin
                    admin = User.objects.filter(is_staff=True).first()
                    notification = PaymentTransactionNotification.objects.create(
                        reference_code=transaction.transaction_id[:16],
                        sender=user,
                        receiver=admin,
                        notification_type='compliance_required',
                        amount=amount,
                        currency=currency,
                        full_message=f"KYC verification requested: ${amount} from {user.email}",
                        short_message=f"📋 KYC requested: ${amount}",
                        emoji='📋'
                    )
                    
                    return {
                        'success': True,
                        'transaction_id': transaction.transaction_id,
                        'kyc_id': result['kyc_id'],
                        'message': 'KYC verification requested. Please wait for admin review.'
                    }
                else:
                    transaction.delete()
                    return {'success': False, 'error': result.get('error')}
                
        except Exception as e:
            logger.error(f"KYC request failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def submit_kyc_form(compliance_id, form_data, documents=None):
        """Submit KYC form data to compliance app"""
        try:
            data = {
                'compliance_id': compliance_id,
                'form_data': form_data,
                'documents': documents or []
            }
            
            result = ComplianceIntegrationService._call_compliance_api(
                'kyc/submit/',
                data
            )
            
            return result
            
        except Exception as e:
            logger.error(f"KYC form submission failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_compliance_status(compliance_id):
        """Check status of compliance request"""
        try:
            result = ComplianceIntegrationService._call_compliance_api(
                f'requests/{compliance_id}/status/',
                method='GET'
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Status check failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def generate_tac_for_transaction(compliance_id, admin_user):
        """Request TAC generation from compliance app"""
        try:
            data = {
                'compliance_id': compliance_id,
                'admin_user_id': str(admin_user.id),
                'purpose': 'manual_payment_release'
            }
            
            result = ComplianceIntegrationService._call_compliance_api(
                'tac/generate/',
                data
            )
            
            return result
            
        except Exception as e:
            logger.error(f"TAC generation failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def verify_tac_code(compliance_id, tac_code, user):
        """Verify TAC code with compliance app"""
        try:
            data = {
                'compliance_id': compliance_id,
                'tac_code': tac_code,
                'user_id': str(user.id)
            }
            
            result = ComplianceIntegrationService._call_compliance_api(
                'tac/verify/',
                data
            )
            
            if result.get('success') and result.get('valid'):
                # Update transaction status
                transaction = Transaction.objects.filter(
                    compliance_reference=compliance_id
                ).first()
                
                if transaction:
                    transaction.status = 'completed'
                    transaction.save()
                    
                    # Create completion notification
                    PaymentTransactionNotification.objects.create(
                        reference_code=transaction.transaction_id[:16],
                        sender=user,
                        receiver=user,
                        notification_type='payment_completed',
                        amount=transaction.amount,
                        currency=transaction.currency,
                        full_message=f"{transaction.transaction_id} Confirmed! You have received ${transaction.amount}.",
                        short_message=f"✅ +${transaction.amount} (Manual Payment)",
                        emoji='✅'
                    )
                    
                    # Activity feed
                    ActivityFeed.objects.create(
                        user=user,
                        activity_type='payment_received',
                        reference=transaction.transaction_id,
                        amount=transaction.amount,
                        display_text=f"✅ +${transaction.amount} (Manual Payment)",
                        emoji='✅',
                        color_class='text-green-600'
                    )
            
            return result
            
        except Exception as e:
            logger.error(f"TAC verification failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_pending_approvals():
        """Get list of pending approvals from compliance app"""
        try:
            result = ComplianceIntegrationService._call_compliance_api(
                'requests/pending/',
                method='GET'
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get pending approvals: {str(e)}")
            return {'success': False, 'error': str(e), 'pending_requests': []}
    
    @staticmethod
    def approve_compliance_request(compliance_id, admin_user, notes=""):
        """Approve a compliance request"""
        try:
            data = {
                'compliance_id': compliance_id,
                'admin_user_id': str(admin_user.id),
                'notes': notes,
                'action': 'approve'
            }
            
            result = ComplianceIntegrationService._call_compliance_api(
                'requests/approve/',
                data
            )
            
            if result.get('success'):
                # Update transaction status
                transaction = Transaction.objects.filter(
                    compliance_reference=compliance_id
                ).first()
                
                if transaction:
                    transaction.status = 'compliance_approved'
                    transaction.save()
            
            return result
            
        except Exception as e:
            logger.error(f"Approval failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def reject_compliance_request(compliance_id, admin_user, reason=""):
        """Reject a compliance request"""
        try:
            data = {
                'compliance_id': compliance_id,
                'admin_user_id': str(admin_user.id),
                'reason': reason,
                'action': 'reject'
            }
            
            result = ComplianceIntegrationService._call_compliance_api(
                'requests/reject/',
                data
            )
            
            if result.get('success'):
                # Update transaction status
                transaction = Transaction.objects.filter(
                    compliance_reference=compliance_id
                ).first()
                
                if transaction:
                    transaction.status = 'cancelled'
                    transaction.save()
            
            return result
            
        except Exception as e:
            logger.error(f"Rejection failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def schedule_video_call(compliance_id, call_datetime, call_link, admin_user):
        """Schedule video call through compliance app"""
        try:
            data = {
                'compliance_id': compliance_id,
                'call_datetime': call_datetime.isoformat(),
                'call_link': call_link,
                'admin_user_id': str(admin_user.id)
            }
            
            result = ComplianceIntegrationService._call_compliance_api(
                'video-call/schedule/',
                data
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Video call scheduling failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def complete_video_call(compliance_id, approved=True, admin_notes=""):
        """Complete video call verification"""
        try:
            data = {
                'compliance_id': compliance_id,
                'approved': approved,
                'admin_notes': admin_notes
            }
            
            result = ComplianceIntegrationService._call_compliance_api(
                'video-call/complete/',
                data
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Video call completion failed: {str(e)}")
            return {'success': False, 'error': str(e)}