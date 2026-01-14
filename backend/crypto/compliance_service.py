# crypto/compliance_service.py - INTEGRATION WITH CENTRAL COMPLIANCE

import requests
import logging
from django.conf import settings
from django.core.cache import cache
from decimal import Decimal
import json

logger = logging.getLogger(__name__)


class CryptoComplianceService:
    """Service to handle all crypto compliance interactions with central system"""
    
    COMPLIANCE_API_BASE = getattr(settings, 'COMPLIANCE_API_URL', 'http://localhost:8000/compliance/api/')
    APP_NAME = 'crypto'
    
    @classmethod
    def _make_compliance_request(cls, endpoint, data, method='POST'):
        """Make API call to central compliance system"""
        try:
            headers = {
                'X-App-Name': cls.APP_NAME,
                'X-API-Key': getattr(settings, 'COMPLIANCE_API_KEY', 'crypto-app-key'),
                'Content-Type': 'application/json'
            }
            
            url = f"{cls.COMPLIANCE_API_BASE.rstrip('/')}/{endpoint.lstrip('/')}"
            
            if method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'GET':
                response = requests.get(url, params=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            
            response.raise_for_status()
            return response.json()
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Compliance API request failed: {str(e)}")
            # Fallback mode - log but don't block transactions
            return {'success': False, 'error': str(e), 'fallback': True}
        except Exception as e:
            logger.error(f"Unexpected error in compliance request: {str(e)}")
            return {'success': False, 'error': str(e), 'fallback': True}
    
    @classmethod
    def request_kyc_for_transaction(cls, transaction_id, user_id, amount, currency='USD', reason=''):
        """Request KYC verification for crypto transaction"""
        data = {
            'app_name': cls.APP_NAME,
            'app_object_id': str(transaction_id),
            'app_object_type': 'crypto_transaction',
            'user_id': str(user_id),
            'amount': str(amount),
            'currency': currency,
            'request_type': 'kyc_verification',
            'reason': reason or f'High-value crypto transaction: {amount} {currency}',
            'metadata': {
                'transaction_type': 'crypto',
                'requires_video_call': Decimal(str(amount)) > Decimal('50000'),
                'priority': 'high' if Decimal(str(amount)) > Decimal('50000') else 'medium'
            }
        }
        
        response = cls._make_compliance_request('requests/create/', data)
        
        if response and 'compliance_reference' in response:
            return {
                'success': True,
                'compliance_reference': response['compliance_reference'],
                'requires_action': response.get('requires_action', False),
                'message': response.get('message', 'KYC verification requested')
            }
        return {'success': False, 'error': 'Failed to create compliance request'}
    
    @classmethod
    def flag_suspicious_transaction(cls, transaction_id, user_id, indicators, reason):
        """Flag suspicious crypto transaction for compliance review"""
        data = {
            'app_name': cls.APP_NAME,
            'app_object_id': str(transaction_id),
            'app_object_type': 'crypto_transaction',
            'user_id': str(user_id),
            'request_type': 'suspicious_activity',
            'reason': reason,
            'metadata': {
                'suspicious_indicators': indicators,
                'source': 'crypto_aml_engine',
                'requires_urgent_review': True
            }
        }
        
        response = cls._make_compliance_request('requests/create/', data)
        
        if response and 'compliance_reference' in response:
            return {
                'success': True,
                'compliance_reference': response['compliance_reference'],
                'message': 'Transaction flagged for compliance review'
            }
        return {'success': False, 'error': 'Failed to flag transaction'}
    
    @classmethod
    def request_tac_verification(cls, transaction_id, user_id, recipient_address=None, amount=None):
        """Request TAC verification for crypto withdrawal"""
        data = {
            'app_name': cls.APP_NAME,
            'app_object_id': str(transaction_id),
            'app_object_type': 'crypto_transaction',
            'user_id': str(user_id),
            'request_type': 'tac_verification',
            'metadata': {
                'action': 'crypto_withdrawal',
                'recipient_address': recipient_address,
                'amount': str(amount) if amount else None
            }
        }
        
        response = cls._make_compliance_request('tac/generate/', data)
        return response
    
    @classmethod
    def verify_tac_code(cls, compliance_reference, tac_code, user_id):
        """Verify TAC code with compliance system"""
        data = {
            'compliance_reference': compliance_reference,
            'tac_code': tac_code,
            'user_id': str(user_id)
        }
        
        response = cls._make_compliance_request('tac/verify/', data)
        return response
    
    @classmethod
    def check_compliance_status(cls, compliance_reference):
        """Check status of compliance request"""
        cache_key = f'crypto_compliance_status_{compliance_reference}'
        cached_status = cache.get(cache_key)
        
        if cached_status:
            return cached_status
        
        try:
            response = cls._make_compliance_request(
                f'requests/{compliance_reference}/status/',
                {},
                method='GET'
            )
            
            if response and 'status' in response:
                cache.set(cache_key, response, timeout=30)  # Cache for 30 seconds
                return response
                
        except Exception as e:
            logger.error(f"Status check failed: {str(e)}")
        
        return {'status': 'unknown', 'message': 'Could not fetch status'}
    
    @classmethod
    def schedule_video_verification(cls, compliance_reference, user_id, preferred_time=None, timezone="UTC"):
        """Schedule video verification for crypto transaction"""
        data = {
            'compliance_reference': compliance_reference,
            'user_id': str(user_id),
            'request_type': 'video_verification',
            'metadata': {
                'preferred_time': preferred_time.isoformat() if preferred_time else None,
                'timezone': timezone,
                'verification_type': 'crypto_transaction'
            }
        }
        
        response = cls._make_compliance_request('video-call/schedule/', data)
        return response
    
    @classmethod
    def submit_compliance_documents(cls, compliance_reference, user_id, documents):
        """Submit compliance documents for verification"""
        data = {
            'compliance_reference': compliance_reference,
            'user_id': str(user_id),
            'documents': documents,
            'request_type': 'document_submission'
        }
        
        response = cls._make_compliance_request('documents/submit/', data)
        return response
    
    @classmethod
    def get_pending_compliance_requests(cls):
        """Get all pending crypto compliance requests"""
        data = {
            'app_name': cls.APP_NAME,
            'status': 'pending'
        }
        
        response = cls._make_compliance_request('requests/pending/', data, method='GET')
        return response.get('requests', []) if response else []
    
    @classmethod
    def approve_compliance_request(cls, compliance_reference, admin_user_id, notes=""):
        """Approve a compliance request"""
        data = {
            'compliance_reference': compliance_reference,
            'admin_user_id': str(admin_user_id),
            'notes': notes,
            'action': 'approve'
        }
        
        response = cls._make_compliance_request('requests/approve/', data)
        return response
    
    @classmethod
    def reject_compliance_request(cls, compliance_reference, admin_user_id, reason=""):
        """Reject a compliance request"""
        data = {
            'compliance_reference': compliance_reference,
            'admin_user_id': str(admin_user_id),
            'reason': reason,
            'action': 'reject'
        }
        
        response = cls._make_compliance_request('requests/reject/', data)
        return response
    
    @classmethod
    def complete_video_call(cls, compliance_reference, approved=True, admin_notes=""):
        """Complete video call verification"""
        data = {
            'compliance_reference': compliance_reference,
            'approved': approved,
            'admin_notes': admin_notes
        }
        
        response = cls._make_compliance_request('video-call/complete/', data)
        return response