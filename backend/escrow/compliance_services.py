# escrow/compliance_services.py - COMPLIANCE INTEGRATION SERVICE

from django.db import transaction as db_transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal
import logging
import requests
from django.conf import settings
from .models import Escrow, EscrowLog

logger = logging.getLogger(__name__)
User = get_user_model()


class EscrowComplianceService:
    """Service for integrating escrow with central compliance app"""
    
    @staticmethod
    def _call_compliance_api(endpoint, data=None, method='POST'):
        """Make API call to compliance app"""
        try:
            # Get compliance app URL from settings
            base_url = getattr(settings, 'COMPLIANCE_API_URL', 'http://localhost:8000/compliance/api/')
            
            url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
            
            headers = {
                'Content-Type': 'application/json',
                'X-App-Name': 'escrow',
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
            logger.error(f"Escrow Compliance API call failed: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected error calling compliance API: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def request_dispute_resolution(escrow, user, reason, dispute_details=None):
        """Request compliance intervention for escrow dispute"""
        try:
            with db_transaction.atomic():
                # Update escrow dispute status
                escrow.dispute_status = 'under_review'
                escrow.requires_compliance_approval = True
                escrow.save()
                
                # Call compliance app to create dispute resolution request
                compliance_data = {
                    'app_name': 'escrow',
                    'app_object_id': str(escrow.id),
                    'app_escrow_id': escrow.escrow_id,
                    'user_id': str(user.id),
                    'user_name': user.username,
                    'amount': str(escrow.amount),
                    'currency': escrow.currency,
                    'request_type': 'dispute_resolution',
                    'description': f"Escrow dispute: {reason}",
                    'metadata': {
                        'sender_id': escrow.sender_id,
                        'sender_name': escrow.sender_name,
                        'receiver_id': escrow.receiver_id,
                        'receiver_name': escrow.receiver_name,
                        'escrow_title': escrow.title,
                        'dispute_reason': reason,
                        'dispute_details': dispute_details or {},
                        'requires_video_call': True,
                        'requires_tac': True,
                    }
                }
                
                # Call compliance API
                result = EscrowComplianceService._call_compliance_api(
                    'requests/create/',
                    compliance_data
                )
                
                if result.get('success'):
                    # Update escrow with compliance reference
                    escrow.compliance_reference = result['compliance_id']
                    escrow.save()
                    
                    # Log the compliance request
                    EscrowLog.objects.create(
                        escrow=escrow,
                        user_id=str(user.id),
                        user_name=user.username,
                        action='compliance_requested',
                        details=f"Compliance requested for dispute resolution. Reference: {result['compliance_id']}",
                        ip_address=None
                    )
                    
                    return {
                        'success': True,
                        'compliance_id': result['compliance_id'],
                        'message': 'Dispute submitted for compliance review.',
                        'escrow_id': escrow.escrow_id
                    }
                else:
                    # Rollback escrow status if compliance request failed
                    escrow.dispute_status = 'opened'
                    escrow.requires_compliance_approval = False
                    escrow.save()
                    return {
                        'success': False,
                        'error': f"Compliance request failed: {result.get('error')}"
                    }
                
        except Exception as e:
            logger.error(f"Dispute resolution request failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def request_kyc_for_high_value(escrow, user):
        """Request KYC verification for high-value escrow"""
        try:
            with db_transaction.atomic():
                # Mark escrow as requiring compliance approval
                escrow.requires_compliance_approval = True
                escrow.save()
                
                # Determine which party needs KYC (sender for high amount)
                compliance_data = {
                    'app_name': 'escrow',
                    'app_object_id': str(escrow.id),
                    'app_escrow_id': escrow.escrow_id,
                    'user_id': str(user.id),
                    'user_name': user.username,
                    'amount': str(escrow.amount),
                    'currency': escrow.currency,
                    'request_type': 'kyc_verification',
                    'description': f"High-value escrow KYC: {escrow.title}",
                    'metadata': {
                        'sender_id': escrow.sender_id,
                        'sender_name': escrow.sender_name,
                        'receiver_id': escrow.receiver_id,
                        'receiver_name': escrow.receiver_name,
                        'escrow_title': escrow.title,
                        'kyc_type': 'enhanced',
                        'requires_video_call': escrow.amount > Decimal('50000'),
                        'threshold_amount': '10000',
                    }
                }
                
                # Call compliance API
                result = EscrowComplianceService._call_compliance_api(
                    'kyc/request/',
                    compliance_data
                )
                
                if result.get('success'):
                    escrow.compliance_reference = result['kyc_id']
                    escrow.save()
                    
                    # Log the KYC request
                    EscrowLog.objects.create(
                        escrow=escrow,
                        user_id=str(user.id),
                        user_name=user.username,
                        action='compliance_requested',
                        details=f"KYC requested for high-value escrow. Reference: {result['kyc_id']}",
                        ip_address=None
                    )
                    
                    return {
                        'success': True,
                        'compliance_id': result['kyc_id'],
                        'message': 'KYC verification requested for high-value escrow.',
                        'escrow_id': escrow.escrow_id
                    }
                else:
                    escrow.requires_compliance_approval = False
                    escrow.save()
                    return {'success': False, 'error': result.get('error')}
                
        except Exception as e:
            logger.error(f"KYC request failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_compliance_status(compliance_id):
        """Check status of compliance request"""
        try:
            result = EscrowComplianceService._call_compliance_api(
                f'requests/{compliance_id}/status/',
                method='GET'
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Status check failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def submit_compliance_form(compliance_id, form_data, user):
        """Submit compliance form data for escrow dispute"""
        try:
            data = {
                'compliance_id': compliance_id,
                'form_data': form_data,
                'user_id': str(user.id)
            }
            
            result = EscrowComplianceService._call_compliance_api(
                'forms/submit/',
                data
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Form submission failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def verify_tac_for_release(compliance_id, tac_code, user):
        """Verify TAC code for escrow release after compliance approval"""
        try:
            data = {
                'compliance_id': compliance_id,
                'tac_code': tac_code,
                'user_id': str(user.id)
            }
            
            result = EscrowComplianceService._call_compliance_api(
                'tac/verify/',
                data
            )
            
            if result.get('success') and result.get('valid'):
                # Find escrow by compliance reference
                escrow = Escrow.objects.filter(
                    compliance_reference=compliance_id
                ).first()
                
                if escrow:
                    # Release escrow if TAC verified
                    success = escrow.release()
                    if success:
                        # Log the compliance-approved release
                        EscrowLog.objects.create(
                            escrow=escrow,
                            user_id=str(user.id),
                            user_name=user.username,
                            action='compliance_approved',
                            details=f"Escrow released after compliance approval. TAC verified.",
                            ip_address=None
                        )
            
            return result
            
        except Exception as e:
            logger.error(f"TAC verification failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def request_manual_release_approval(escrow, user, reason):
        """Request manual release approval for special cases"""
        try:
            with db_transaction.atomic():
                # Mark escrow as requiring compliance approval
                escrow.requires_compliance_approval = True
                escrow.save()
                
                compliance_data = {
                    'app_name': 'escrow',
                    'app_object_id': str(escrow.id),
                    'app_escrow_id': escrow.escrow_id,
                    'user_id': str(user.id),
                    'user_name': user.username,
                    'amount': str(escrow.amount),
                    'currency': escrow.currency,
                    'request_type': 'manual_release',
                    'description': f"Manual release request: {reason}",
                    'metadata': {
                        'sender_id': escrow.sender_id,
                        'sender_name': escrow.sender_name,
                        'receiver_id': escrow.receiver_id,
                        'receiver_name': escrow.receiver_name,
                        'escrow_title': escrow.title,
                        'reason': reason,
                        'requires_tac': True,
                        'requires_review': True,
                    }
                }
                
                result = EscrowComplianceService._call_compliance_api(
                    'requests/create/',
                    compliance_data
                )
                
                if result.get('success'):
                    escrow.compliance_reference = result['compliance_id']
                    escrow.save()
                    
                    EscrowLog.objects.create(
                        escrow=escrow,
                        user_id=str(user.id),
                        user_name=user.username,
                        action='compliance_requested',
                        details=f"Manual release approval requested. Reference: {result['compliance_id']}",
                        ip_address=None
                    )
                    
                    return {
                        'success': True,
                        'compliance_id': result['compliance_id'],
                        'message': 'Manual release request submitted for compliance review.',
                        'escrow_id': escrow.escrow_id
                    }
                else:
                    escrow.requires_compliance_approval = False
                    escrow.save()
                    return {'success': False, 'error': result.get('error')}
                
        except Exception as e:
            logger.error(f"Manual release request failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_pending_compliance_requests():
        """Get list of pending escrow compliance requests"""
        try:
            # Filter for escrow-specific requests
            data = {'app_name': 'escrow'}
            result = EscrowComplianceService._call_compliance_api(
                'requests/pending/',
                data=data,
                method='GET'
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get pending requests: {str(e)}")
            return {'success': False, 'error': str(e), 'pending_requests': []}