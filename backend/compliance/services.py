"""
compliance/services.py - Business logic and utility functions for compliance app
"""

import secrets
import hashlib
import os
import mimetypes
from datetime import timedelta
from django.utils import timezone
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.db import transaction
import logging

from .models import (
    KYCVerification, KYCDocument, TACCode,
    ComplianceAuditLog, WithdrawalRequest, VerificationStatus,
    DocumentType, ComplianceCheck
)

logger = logging.getLogger(__name__)


def generate_tac_code():
    """Generate a secure 6-digit TAC code"""
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])


def hash_file(file_path):
    """Generate SHA256 hash of file for verification"""
    sha256_hash = hashlib.sha256()
    
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error hashing file {file_path}: {e}")
        return None


def save_upload_file(upload_file, user_id, doc_type):
    """Save uploaded file and return path, hash, and size"""
    try:
        # Create secure directory structure
        timestamp = int(timezone.now().timestamp())
        safe_user_id = str(user_id).replace('/', '_').replace('\\', '_')
        safe_doc_type = str(doc_type).replace('/', '_').replace('\\', '_')
        
        # Create directory if it doesn't exist
        user_dir = f"compliance/documents/{safe_user_id}/{timestamp}"
        os.makedirs(os.path.join(settings.MEDIA_ROOT, user_dir), exist_ok=True)
        
        # Generate secure filename
        file_extension = os.path.splitext(upload_file.name)[1].lower()
        if not file_extension:
            # Determine extension from content type
            content_type = upload_file.content_type
            file_extension = mimetypes.guess_extension(content_type) or '.bin'
        
        # Generate unique filename
        unique_id = secrets.token_hex(8)
        safe_filename = f"{safe_doc_type}_{unique_id}{file_extension}"
        file_path = os.path.join(user_dir, safe_filename)
        
        # Save file using Django storage
        saved_path = default_storage.save(file_path, ContentFile(upload_file.read()))
        
        # Get absolute path for hashing
        if hasattr(default_storage, 'path'):
            full_path = default_storage.path(saved_path)
        else:
            full_path = os.path.join(settings.MEDIA_ROOT, saved_path)
        
        # Calculate file hash and size
        file_hash = hash_file(full_path)
        file_size = upload_file.size
        
        logger.info(f"File saved: {saved_path}, size: {file_size} bytes, hash: {file_hash}")
        
        return saved_path, file_hash, file_size
    
    except Exception as e:
        logger.error(f"Error saving upload file: {e}")
        raise


def log_compliance_action(user_id, action, action_type, entity_type, entity_id,
                         old_value=None, new_value=None, ip_address=None,
                         actor_id=None, actor_role=None, notes=None):
    """Log compliance actions for audit trail"""
    try:
        audit_log = ComplianceAuditLog.objects.create(
            user_id=user_id,
            action=action,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_value,
            new_value=new_value,
            actor_id=actor_id,
            actor_role=actor_role,
            ip_address=ip_address,
            notes=notes
        )
        
        logger.info(f"Compliance action logged: {action} for user {user_id}")
        return audit_log
    
    except Exception as e:
        logger.error(f"Error logging compliance action: {e}")
        return None


def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    
    return ip


def perform_compliance_checks(verification_id):
    """Perform automated compliance checks on a verification"""
    try:
        verification = KYCVerification.objects.get(id=verification_id)
        
        checks = []
        
        # 1. PEP (Politically Exposed Person) Check
        pep_check = perform_pep_check(verification)
        checks.append(pep_check)
        
        # 2. Sanctions Check
        sanctions_check = perform_sanctions_check(verification)
        checks.append(sanctions_check)
        
        # 3. Document Authenticity Check
        document_check = perform_document_check(verification)
        checks.append(document_check)
        
        # 4. Risk Assessment
        risk_check = perform_risk_assessment(verification)
        checks.append(risk_check)
        
        # Calculate overall risk score
        total_risk_score = sum(check.risk_score for check in checks)
        verification.risk_score = total_risk_score
        
        # Determine risk level
        if total_risk_score >= 70:
            verification.risk_level = 'high'
        elif total_risk_score >= 30:
            verification.risk_level = 'medium'
        else:
            verification.risk_level = 'low'
        
        verification.save()
        
        logger.info(f"Compliance checks completed for verification {verification_id}")
        return checks
    
    except Exception as e:
        logger.error(f"Error performing compliance checks: {e}")
        return []


def perform_pep_check(verification):
    """Check if user is a Politically Exposed Person (mock implementation)"""
    try:
        # This is a mock implementation
        # In production, integrate with a PEP database
        pep_keywords = [
            'minister', 'senator', 'congress', 'parliament', 'diplomat',
            'judge', 'military', 'government', 'official'
        ]
        
        occupation = (verification.occupation or '').lower()
        is_pep = any(keyword in occupation for keyword in pep_keywords)
        
        check = ComplianceCheck.objects.create(
            verification=verification,
            user_id=verification.user_id,
            check_type='pep_check',
            status='completed',
            result={'is_pep': is_pep, 'matched_keywords': pep_keywords},
            risk_score=50 if is_pep else 0,
            matches_found=1 if is_pep else 0,
            provider='internal',
            provider_reference=f"PEP_CHECK_{verification.id}",
            expires_at=timezone.now() + timedelta(days=365)
        )
        
        return check
    
    except Exception as e:
        logger.error(f"Error performing PEP check: {e}")
        return None


def perform_sanctions_check(verification):
    """Check if user is on sanctions lists (mock implementation)"""
    try:
        # This is a mock implementation
        # In production, integrate with sanctions databases
        sanctions_list = [
            {'name': 'John Doe', 'country': 'US'},
            {'name': 'Jane Smith', 'country': 'GB'},
        ]
        
        full_name = f"{verification.first_name} {verification.last_name}".lower()
        is_sanctioned = any(
            sanction['name'].lower() in full_name and 
            sanction['country'] == verification.country_of_residence
            for sanction in sanctions_list
        )
        
        check = ComplianceCheck.objects.create(
            verification=verification,
            user_id=verification.user_id,
            check_type='sanctions_check',
            status='completed',
            result={'is_sanctioned': is_sanctioned, 'list_checked': 'internal'},
            risk_score=100 if is_sanctioned else 0,
            matches_found=1 if is_sanctioned else 0,
            provider='internal',
            provider_reference=f"SANCTIONS_CHECK_{verification.id}",
            expires_at=timezone.now() + timedelta(days=30)
        )
        
        return check
    
    except Exception as e:
        logger.error(f"Error performing sanctions check: {e}")
        return None


def perform_document_check(verification):
    """Check document validity (mock implementation)"""
    try:
        documents = verification.documents.all()
        
        # Check if all required documents are present
        required_docs = [DocumentType.PASSPORT, DocumentType.NATIONAL_ID]
        has_required = any(doc.document_type in required_docs for doc in documents)
        
        # Check document expiration
        expired_docs = []
        for doc in documents:
            if doc.verified_at and (timezone.now() - doc.verified_at).days > 365:
                expired_docs.append(str(doc.id))
        
        risk_score = 0
        if not has_required:
            risk_score += 40
        if expired_docs:
            risk_score += 30
        
        check = ComplianceCheck.objects.create(
            verification=verification,
            user_id=verification.user_id,
            check_type='document_check',
            status='completed',
            result={
                'has_required_documents': has_required,
                'expired_documents': expired_docs,
                'total_documents': documents.count()
            },
            risk_score=risk_score,
            matches_found=len(expired_docs),
            provider='internal',
            provider_reference=f"DOCUMENT_CHECK_{verification.id}",
            expires_at=timezone.now() + timedelta(days=180)
        )
        
        return check
    
    except Exception as e:
        logger.error(f"Error performing document check: {e}")
        return None


def perform_risk_assessment(verification):
    """Perform comprehensive risk assessment"""
    try:
        risk_factors = []
        total_risk_score = 0
        
        # Country risk
        high_risk_countries = ['AF', 'IR', 'KP', 'SY', 'YE']
        if verification.country_of_residence in high_risk_countries:
            risk_factors.append({'factor': 'high_risk_country', 'score': 30})
            total_risk_score += 30
        
        # Age risk
        age = (timezone.now().date() - verification.date_of_birth.date()).days // 365
        if age < 25:
            risk_factors.append({'factor': 'young_age', 'score': 15})
            total_risk_score += 15
        elif age > 65:
            risk_factors.append({'factor': 'senior_age', 'score': 10})
            total_risk_score += 10
        
        # Occupation risk
        high_risk_occupations = ['cash business', 'gambling', 'adult entertainment']
        occupation = (verification.occupation or '').lower()
        if any(risk_occ in occupation for risk_occ in high_risk_occupations):
            risk_factors.append({'factor': 'high_risk_occupation', 'score': 25})
            total_risk_score += 25
        
        # Source of funds risk
        vague_sources = ['gift', 'inheritance', 'savings']
        source = (verification.source_of_funds or '').lower()
        if any(vague in source for vague in vague_sources):
            risk_factors.append({'factor': 'vague_source_of_funds', 'score': 20})
            total_risk_score += 20
        
        check = ComplianceCheck.objects.create(
            verification=verification,
            user_id=verification.user_id,
            check_type='risk_assessment',
            status='completed',
            result={
                'risk_factors': risk_factors,
                'total_risk_score': total_risk_score,
                'age': age
            },
            risk_score=total_risk_score,
            matches_found=len(risk_factors),
            provider='internal',
            provider_reference=f"RISK_ASSESSMENT_{verification.id}",
            expires_at=timezone.now() + timedelta(days=90)
        )
        
        return check
    
    except Exception as e:
        logger.error(f"Error performing risk assessment: {e}")
        return None


def validate_withdrawal_request(user_id, amount, currency):
    """Validate withdrawal request"""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Check daily limit
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_withdrawals = WithdrawalRequest.objects.filter(
            user_id=user_id,
            created_at__gte=today_start,
            status__in=['completed', 'processing']
        )
        
        daily_total = sum(w.amount for w in today_withdrawals)
        daily_limit = getattr(settings, 'WITHDRAWAL_DAILY_LIMIT', 10000)
        
        if daily_total + amount > daily_limit:
            return False, f"Daily withdrawal limit exceeded. Limit: {daily_limit}, Used: {daily_total}"
        
        # Check monthly limit
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_withdrawals = WithdrawalRequest.objects.filter(
            user_id=user_id,
            created_at__gte=month_start,
            status__in=['completed', 'processing']
        )
        
        monthly_total = sum(w.amount for w in month_withdrawals)
        monthly_limit = getattr(settings, 'WITHDRAWAL_MONTHLY_LIMIT', 50000)
        
        if monthly_total + amount > monthly_limit:
            return False, f"Monthly withdrawal limit exceeded. Limit: {monthly_limit}, Used: {monthly_total}"
        
        # Check minimum amount
        minimum_amount = getattr(settings, 'WITHDRAWAL_MINIMUM_AMOUNT', 10)
        if amount < minimum_amount:
            return False, f"Minimum withdrawal amount is {minimum_amount}"
        
        return True, "Validation successful"
    
    except Exception as e:
        logger.error(f"Error validating withdrawal request: {e}")
        return False, str(e)


@transaction.atomic
def process_withdrawal(withdrawal_id, processor_id):
    """Process a withdrawal request"""
    try:
        withdrawal = WithdrawalRequest.objects.select_for_update().get(id=withdrawal_id)
        
        if withdrawal.status != 'processing':
            return False, "Withdrawal is not in processing status"
        
        # Update withdrawal status
        withdrawal.status = 'completed'
        withdrawal.processed_by = processor_id
        withdrawal.processed_at = timezone.now()
        withdrawal.completed_at = timezone.now()
        
        # Generate transaction hash (mock)
        withdrawal.transaction_hash = f"TX_{secrets.token_hex(16)}"
        
        withdrawal.save()
        
        # Log the action
        log_compliance_action(
            withdrawal.user_id,
            "Withdrawal Processed",
            "withdrawal_processing",
            "withdrawal",
            str(withdrawal.id),
            old_value={"status": "processing"},
            new_value={"status": "completed", "transaction_hash": withdrawal.transaction_hash},
            actor_id=processor_id,
            actor_role="processor"
        )
        
        logger.info(f"Withdrawal {withdrawal_id} processed successfully")
        return True, "Withdrawal processed successfully"
    
    except Exception as e:
        logger.error(f"Error processing withdrawal {withdrawal_id}: {e}")
        return False, str(e)


def get_user_compliance_status(user_id):
    """Get comprehensive compliance status for a user"""
    try:
        verification = KYCVerification.objects.filter(
            user_id=user_id
        ).order_by('-created_at').first()
        
        if not verification:
            return {
                'kyc_status': 'not_started',
                'risk_level': 'unknown',
                'withdrawal_limits': {
                    'daily': 0,
                    'monthly': 0,
                    'used_today': 0,
                    'used_this_month': 0
                },
                'restrictions': ['kyc_required'],
                'compliance_score': 0
            }
        
        # Calculate withdrawal usage
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        withdrawals = WithdrawalRequest.objects.filter(
            user_id=user_id,
            status__in=['completed', 'processing']
        )
        
        used_today = sum(
            w.amount for w in withdrawals.filter(created_at__gte=today_start)
        )
        
        used_this_month = sum(
            w.amount for w in withdrawals.filter(created_at__gte=month_start)
        )
        
        # Get limits based on compliance level
        limits = get_limits_for_compliance_level(verification.compliance_level)
        
        # Calculate compliance score (0-100)
        compliance_score = calculate_compliance_score(verification)
        
        # Determine restrictions
        restrictions = []
        if verification.verification_status != VerificationStatus.APPROVED:
            restrictions.append('kyc_pending')
        if verification.risk_level == 'high':
            restrictions.append('enhanced_monitoring')
        if used_today >= limits['daily']:
            restrictions.append('daily_limit_reached')
        if used_this_month >= limits['monthly']:
            restrictions.append('monthly_limit_reached')
        
        return {
            'kyc_status': verification.verification_status,
            'compliance_level': verification.compliance_level,
            'risk_level': verification.risk_level,
            'verified_at': verification.verified_at.isoformat() if verification.verified_at else None,
            'withdrawal_limits': {
                'daily': limits['daily'],
                'monthly': limits['monthly'],
                'used_today': used_today,
                'used_this_month': used_this_month,
                'remaining_today': max(0, limits['daily'] - used_today),
                'remaining_monthly': max(0, limits['monthly'] - used_this_month)
            },
            'restrictions': restrictions,
            'compliance_score': compliance_score,
            'documents_uploaded': verification.documents.count(),
            'last_compliance_check': verification.updated_at.isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting user compliance status: {e}")
        return {
            'error': str(e),
            'kyc_status': 'error',
            'risk_level': 'unknown'
        }


def get_limits_for_compliance_level(compliance_level):
    """Get withdrawal limits based on compliance level"""
    limits = {
        ComplianceLevel.BASIC: {'daily': 1000, 'monthly': 5000},
        ComplianceLevel.STANDARD: {'daily': 5000, 'monthly': 25000},
        ComplianceLevel.ENHANCED: {'daily': 10000, 'monthly': 50000},
        ComplianceLevel.PREMIUM: {'daily': 50000, 'monthly': 250000},
    }
    
    return limits.get(compliance_level, limits[ComplianceLevel.BASIC])


def calculate_compliance_score(verification):
    """Calculate compliance score (0-100)"""
    score = 0
    
    # KYC status
    if verification.verification_status == VerificationStatus.APPROVED:
        score += 40
    elif verification.verification_status == VerificationStatus.IN_REVIEW:
        score += 20
    
    # Documents
    documents_count = verification.documents.count()
    if documents_count >= 3:
        score += 30
    elif documents_count >= 2:
        score += 20
    elif documents_count >= 1:
        score += 10
    
    # Risk level
    if verification.risk_level == 'low':
        score += 20
    elif verification.risk_level == 'medium':
        score += 10
    
    # Compliance level
    if verification.compliance_level == ComplianceLevel.PREMIUM:
        score += 10
    elif verification.compliance_level == ComplianceLevel.ENHANCED:
        score += 7
    elif verification.compliance_level == ComplianceLevel.STANDARD:
        score += 5
    
    return min(score, 100)


def cleanup_expired_tac_codes():
    """Clean up expired TAC codes"""
    try:
        expired_codes = TACCode.objects.filter(
            expires_at__lt=timezone.now(),
            is_used=False,
            is_expired=False
        )
        
        count = expired_codes.update(is_expired=True)
        logger.info(f"Cleaned up {count} expired TAC codes")
        return count
    
    except Exception as e:
        logger.error(f"Error cleaning up expired TAC codes: {e}")
        return 0


def generate_compliance_report(start_date, end_date):
    """Generate compliance report for a date range"""
    try:
        verifications = KYCVerification.objects.filter(
            created_at__range=[start_date, end_date]
        )
        
        withdrawals = WithdrawalRequest.objects.filter(
            created_at__range=[start_date, end_date]
        )
        
        report = {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'kyc_metrics': {
                'total_submissions': verifications.count(),
                'approved': verifications.filter(verification_status=VerificationStatus.APPROVED).count(),
                'rejected': verifications.filter(verification_status=VerificationStatus.REJECTED).count(),
                'pending': verifications.filter(verification_status=VerificationStatus.PENDING).count(),
                'average_processing_time': None,  # Would need to calculate
                'high_risk_count': verifications.filter(risk_level='high').count()
            },
            'withdrawal_metrics': {
                'total_requests': withdrawals.count(),
                'completed': withdrawals.filter(status='completed').count(),
                'pending': withdrawals.filter(status='pending').count(),
                'failed': withdrawals.filter(status='failed').count(),
                'total_amount': sum(w.amount for w in withdrawals),
                'average_amount': None  # Would need to calculate
            },
            'compliance_checks': {
                'total_checks': ComplianceCheck.objects.filter(
                    checked_at__range=[start_date, end_date]
                ).count(),
                'failed_checks': ComplianceCheck.objects.filter(
                    checked_at__range=[start_date, end_date],
                    status='failed'
                ).count()
            },
            'audit_logs': {
                'total_actions': ComplianceAuditLog.objects.filter(
                    created_at__range=[start_date, end_date]
                ).count(),
                'most_common_actions': None  # Would need to calculate
            }
        }
        
        return report
    
    except Exception as e:
        logger.error(f"Error generating compliance report: {e}")
        return {'error': str(e)}