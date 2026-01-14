"""
compliance/services.py - Business logic and services for central compliance app
"""

import secrets
import hashlib
import os
import mimetypes
import requests
from datetime import timedelta
from django.utils import timezone
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.db import transaction
from django.core.mail import send_mail
from django.template.loader import render_to_string
import logging

from .models import (
    ComplianceRequest, KYCVerification, KYCDocument,
    TACRequest, VideoCallSession, ComplianceAuditLog,
    ComplianceAlert, ComplianceRule
)
from .email_service import (
    send_tac_email, send_kyc_approved_email,
    send_kyc_rejected_email, send_video_call_scheduled_email,
    send_compliance_decision_email
)

logger = logging.getLogger(__name__)


class ComplianceService:
    """Service for compliance request operations"""
    
    @staticmethod
    def create_request(user, app_name, request_type, **kwargs):
        """Create a new compliance request"""
        try:
            with transaction.atomic():
                # Create the request
                request_data = {
                    'user': user,
                    'app_name': app_name,
                    'request_type': request_type,
                    'user_email': user.email,
                    'user_phone': kwargs.get('user_phone', ''),
                    'amount': kwargs.get('amount'),
                    'currency': kwargs.get('currency', 'USD'),
                    'description': kwargs.get('description', ''),
                    'form_data': kwargs.get('form_data', {}),
                    'documents': kwargs.get('documents', []),
                    'metadata': kwargs.get('metadata', {}),
                    'ip_address': kwargs.get('ip_address'),
                    'user_agent': kwargs.get('user_agent'),
                }
                
                compliance_request = ComplianceRequest.objects.create(**request_data)
                
                # Run initial risk assessment
                ComplianceService.assess_risk(compliance_request)
                
                # Log the creation
                AuditService.log_action(
                    user=user,
                    action=f"Compliance request created: {request_type}",
                    entity_type='compliance_request',
                    entity_id=compliance_request.compliance_id,
                    new_value={
                        'status': compliance_request.status,
                        'risk_level': compliance_request.risk_level
                    }
                )
                
                # Create alert if high risk
                if compliance_request.risk_level == 'high':
                    AlertService.create_alert(
                        alert_type='risk_threshold',
                        severity='warning',
                        title=f"High risk compliance request: {compliance_request.compliance_id}",
                        description=f"New {request_type} request from {user.email} flagged as high risk",
                        compliance_request=compliance_request,
                        user=user
                    )
                
                return {
                    'success': True,
                    'compliance_id': compliance_request.compliance_id,
                    'status': compliance_request.status,
                    'risk_level': compliance_request.risk_level,
                    'requires_manual_review': compliance_request.requires_manual_review,
                    'requires_tac': compliance_request.requires_tac,
                    'requires_video_call': compliance_request.requires_video_call,
                    'message': 'Compliance request created successfully'
                }
        
        except Exception as e:
            logger.error(f"Error creating compliance request: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def assess_risk(compliance_request):
        """Assess risk for a compliance request"""
        try:
            risk_score = 0
            
            # Amount-based risk
            if compliance_request.amount:
                if compliance_request.amount > 10000:
                    risk_score += 50
                elif compliance_request.amount > 5000:
                    risk_score += 30
                elif compliance_request.amount > 1000:
                    risk_score += 15
            
            # User-based risk (simplified - would check user history)
            user_requests = ComplianceRequest.objects.filter(
                user=compliance_request.user,
                created_at__gte=timezone.now() - timedelta(days=30)
            ).count()
            
            if user_requests > 10:
                risk_score += 20
            elif user_requests > 5:
                risk_score += 10
            
            # Time-based risk (unusual hours)
            hour = compliance_request.created_at.hour
            if hour < 6 or hour > 22:  # Outside business hours
                risk_score += 10
            
            # Determine risk level
            if risk_score >= 70:
                risk_level = 'high'
                compliance_request.requires_manual_review = True
                compliance_request.requires_video_call = True
            elif risk_score >= 40:
                risk_level = 'medium'
                compliance_request.requires_manual_review = True
            else:
                risk_level = 'low'
            
            # Set TAC requirement based on amount
            if compliance_request.amount and compliance_request.amount > 1000:
                compliance_request.requires_tac = True
            
            # Update the request
            compliance_request.risk_score = risk_score
            compliance_request.risk_level = risk_level
            compliance_request.priority = 'high' if risk_level == 'high' else 'normal'
            compliance_request.save()
            
            return risk_score, risk_level
        
        except Exception as e:
            logger.error(f"Error assessing risk: {str(e)}")
            return 0, 'low'
    
    @staticmethod
    def approve_request(compliance_request, approved_by, notes=''):
        """Approve a compliance request"""
        try:
            with transaction.atomic():
                # Update request status
                compliance_request.status = 'approved'
                compliance_request.decision = 'approve'
                compliance_request.reviewed_by = approved_by
                compliance_request.reviewed_at = timezone.now()
                compliance_request.resolved_at = timezone.now()
                compliance_request.decision_notes = notes
                compliance_request.save()
                
                # Log the approval
                AuditService.log_action(
                    user=approved_by,
                    action=f"Compliance request approved: {compliance_request.compliance_id}",
                    entity_type='compliance_request',
                    entity_id=compliance_request.compliance_id,
                    old_value={'status': 'pending'},
                    new_value={'status': 'approved', 'reviewed_by': approved_by.email}
                )
                
                # Send notification to user
                send_compliance_decision_email(
                    to_email=compliance_request.user_email,
                    user_name=compliance_request.user.get_full_name() or compliance_request.user.email,
                    request_type=compliance_request.request_type,
                    decision='approved',
                    notes=notes,
                    compliance_id=compliance_request.compliance_id
                )
                
                return {
                    'success': True,
                    'message': 'Compliance request approved',
                    'compliance_id': compliance_request.compliance_id,
                    'status': compliance_request.status
                }
        
        except Exception as e:
            logger.error(f"Error approving request: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def reject_request(compliance_request, rejected_by, reason, notes=''):
        """Reject a compliance request"""
        try:
            with transaction.atomic():
                # Update request status
                compliance_request.status = 'rejected'
                compliance_request.decision = 'reject'
                compliance_request.reviewed_by = rejected_by
                compliance_request.reviewed_at = timezone.now()
                compliance_request.resolved_at = timezone.now()
                compliance_request.decision_reason = reason
                compliance_request.decision_notes = notes
                compliance_request.save()
                
                # Log the rejection
                AuditService.log_action(
                    user=rejected_by,
                    action=f"Compliance request rejected: {compliance_request.compliance_id}",
                    entity_type='compliance_request',
                    entity_id=compliance_request.compliance_id,
                    old_value={'status': 'pending'},
                    new_value={
                        'status': 'rejected',
                        'reviewed_by': rejected_by.email,
                        'reason': reason
                    }
                )
                
                # Send notification to user
                send_compliance_decision_email(
                    to_email=compliance_request.user_email,
                    user_name=compliance_request.user.get_full_name() or compliance_request.user.email,
                    request_type=compliance_request.request_type,
                    decision='rejected',
                    notes=f"{reason}. {notes}",
                    compliance_id=compliance_request.compliance_id
                )
                
                return {
                    'success': True,
                    'message': 'Compliance request rejected',
                    'compliance_id': compliance_request.compliance_id,
                    'status': compliance_request.status
                }
        
        except Exception as e:
            logger.error(f"Error rejecting request: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def escalate_request(compliance_request, escalated_by, reason):
        """Escalate a compliance request"""
        try:
            # Update request
            compliance_request.status = 'under_review'
            compliance_request.priority = 'high'
            compliance_request.save()
            
            # Create alert for managers
            AlertService.create_alert(
                alert_type='rule_violation',
                severity='warning',
                title=f"Compliance request escalated: {compliance_request.compliance_id}",
                description=f"Request escalated by {escalated_by.email}. Reason: {reason}",
                compliance_request=compliance_request,
                user=escalated_by
            )
            
            # Log the escalation
            AuditService.log_action(
                user=escalated_by,
                action=f"Compliance request escalated: {compliance_request.compliance_id}",
                entity_type='compliance_request',
                entity_id=compliance_request.compliance_id,
                new_value={'status': 'under_review', 'priority': 'high', 'escalation_reason': reason}
            )
            
            return {
                'success': True,
                'message': 'Request escalated successfully',
                'compliance_id': compliance_request.compliance_id,
                'status': compliance_request.status
            }
        
        except Exception as e:
            logger.error(f"Error escalating request: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def request_additional_info(compliance_request, requested_by, info_required):
        """Request additional information for a compliance request"""
        try:
            # Update request
            compliance_request.status = 'info_required'
            compliance_request.review_notes = info_required
            compliance_request.save()
            
            # Create alert for user
            AlertService.create_alert(
                alert_type='deadline_approaching',
                severity='info',
                title=f"Additional information required: {compliance_request.compliance_id}",
                description=info_required,
                compliance_request=compliance_request,
                user=compliance_request.user
            )
            
            # Log the request
            AuditService.log_action(
                user=requested_by,
                action=f"Additional info requested: {compliance_request.compliance_id}",
                entity_type='compliance_request',
                entity_id=compliance_request.compliance_id,
                new_value={'status': 'info_required', 'info_required': info_required}
            )
            
            return {
                'success': True,
                'message': 'Additional information requested',
                'compliance_id': compliance_request.compliance_id,
                'status': compliance_request.status
            }
        
        except Exception as e:
            logger.error(f"Error requesting info: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def evaluate_rule(rule, amount, currency, user, app):
        """Evaluate a compliance rule"""
        try:
            # Check if rule applies to this app
            if rule.applicable_apps != 'all' and rule.applicable_apps != app:
                return False
            
            # Check amount threshold
            if rule.threshold_amount and amount > rule.threshold_amount:
                return True
            
            # Check time period conditions (simplified)
            if rule.time_period:
                # This would check transaction frequency/velocity
                # For now, return False
                pass
            
            # Check other conditions
            if rule.condition:
                # Evaluate JSON conditions
                # This is a simplified implementation
                pass
            
            return False
        
        except Exception as e:
            logger.error(f"Error evaluating rule: {str(e)}")
            return False


class KYCService:
    """Service for KYC verification operations"""
    
    @staticmethod
    def create_verification(user, form_data):
        """Create a new KYC verification"""
        try:
            with transaction.atomic():
                # Create KYC verification
                kyc_data = {
                    'user': user,
                    'first_name': form_data.get('first_name'),
                    'last_name': form_data.get('last_name'),
                    'date_of_birth': form_data.get('date_of_birth'),
                    'nationality': form_data.get('nationality'),
                    'country_of_residence': form_data.get('country_of_residence'),
                    'email': form_data.get('email', user.email),
                    'phone_number': form_data.get('phone_number'),
                    'address_line1': form_data.get('address_line1'),
                    'city': form_data.get('city'),
                    'postal_code': form_data.get('postal_code'),
                    'id_number': form_data.get('id_number'),
                    'id_type': form_data.get('id_type'),
                    'occupation': form_data.get('occupation'),
                    'source_of_funds': form_data.get('source_of_funds'),
                }
                
                kyc_verification = KYCVerification.objects.create(**kyc_data)
                
                # Perform initial checks
                KYCService.perform_initial_checks(kyc_verification)
                
                # Log the creation
                AuditService.log_action(
                    user=user,
                    action='KYC verification submitted',
                    entity_type='kyc_verification',
                    entity_id=kyc_verification.kyc_id,
                    new_value={'status': kyc_verification.verification_status}
                )
                
                return {
                    'success': True,
                    'kyc_id': kyc_verification.kyc_id,
                    'status': kyc_verification.verification_status,
                    'risk_level': kyc_verification.risk_level,
                    'message': 'KYC verification submitted successfully'
                }
        
        except Exception as e:
            logger.error(f"Error creating KYC verification: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def perform_initial_checks(kyc_verification):
        """Perform initial KYC checks"""
        try:
            risk_score = 0
            
            # Age check
            age = kyc_verification.age()
            if age and age < 18:
                risk_score += 100  # Automatic rejection
            elif age and age < 25:
                risk_score += 20
            
            # Country risk check
            high_risk_countries = getattr(settings, 'HIGH_RISK_COUNTRIES', ['AF', 'IR', 'KP', 'SY', 'YE'])
            if kyc_verification.country_of_residence in high_risk_countries:
                risk_score += 40
            
            # PEP check (simplified)
            pep_keywords = ['minister', 'senator', 'government', 'official']
            occupation = (kyc_verification.occupation or '').lower()
            if any(keyword in occupation for keyword in pep_keywords):
                kyc_verification.pep_status = True
                risk_score += 50
            
            # Update risk assessment
            if risk_score >= 70:
                risk_level = 'high'
            elif risk_score >= 40:
                risk_level = 'medium'
            else:
                risk_level = 'low'
            
            kyc_verification.risk_score = risk_score
            kyc_verification.risk_level = risk_level
            kyc_verification.save()
            
            return risk_score, risk_level
        
        except Exception as e:
            logger.error(f"Error performing KYC checks: {str(e)}")
            return 0, 'low'
    
    @staticmethod
    def upload_document(kyc_verification, user, document_data, file):
        """Upload a document for KYC verification"""
        try:
            # Save file
            file_path, file_hash, file_size = DocumentService.save_document(file, user.id, document_data['document_type'])
            
            # Create document record
            document = KYCDocument.objects.create(
                kyc_verification=kyc_verification,
                user=user,
                document_type=document_data['document_type'],
                document_number=document_data.get('document_number'),
                document_name=document_data['document_name'],
                file_name=file_path.split('/')[-1],
                original_file_name=file.name,
                file_path=file_path,
                file_size=file_size,
                file_type=file.content_type,
                file_hash=file_hash,
                issue_date=document_data.get('issue_date'),
                expiry_date=document_data.get('expiry_date'),
                issuing_country=document_data.get('issuing_country'),
                issuing_authority=document_data.get('issuing_authority')
            )
            
            # Update KYC document counts
            kyc_verification.documents_submitted += 1
            kyc_verification.save()
            
            # Log the upload
            AuditService.log_action(
                user=user,
                action='KYC document uploaded',
                entity_type='kyc_document',
                entity_id=document.document_id,
                new_value={
                    'type': document.document_type,
                    'file_name': document.original_file_name
                }
            )
            
            return {
                'success': True,
                'document_id': document.document_id,
                'file_name': document.original_file_name,
                'status': 'uploaded',
                'message': 'Document uploaded successfully'
            }
        
        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def verify_document(document, verified_by, status, notes='', rejection_reason=''):
        """Verify a KYC document"""
        try:
            with transaction.atomic():
                # Update document
                document.status = status
                document.verified_by = verified_by
                document.verified_at = timezone.now()
                document.notes = notes
                document.rejection_reason = rejection_reason if status == 'rejected' else ''
                document.save()
                
                # Update KYC verification counts
                kyc = document.kyc_verification
                if status == 'approved':
                    kyc.documents_approved += 1
                elif status == 'rejected':
                    kyc.documents_rejected += 1
                
                # Check if all documents are approved
                if kyc.documents_approved >= 2:  # At least 2 documents approved
                    kyc.document_verification_completed = True
                
                kyc.save()
                
                # Log the verification
                AuditService.log_action(
                    user=verified_by,
                    action=f'Document {status}: {document.document_id}',
                    entity_type='kyc_document',
                    entity_id=document.document_id,
                    old_value={'status': 'pending'},
                    new_value={'status': status, 'verified_by': verified_by.email}
                )
                
                return {
                    'success': True,
                    'document_id': document.document_id,
                    'status': status,
                    'message': f'Document {status} successfully'
                }
        
        except Exception as e:
            logger.error(f"Error verifying document: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def approve_verification(kyc_verification, approved_by, notes='', compliance_level='standard'):
        """Approve KYC verification"""
        try:
            with transaction.atomic():
                # Update verification
                kyc_verification.verification_status = 'approved'
                kyc_verification.compliance_level = compliance_level
                kyc_verification.verified_by = approved_by
                kyc_verification.verified_at = timezone.now()
                kyc_verification.review_notes = notes
                kyc_verification.save()
                
                # Log the approval
                AuditService.log_action(
                    user=approved_by,
                    action=f'KYC approved: {kyc_verification.kyc_id}',
                    entity_type='kyc_verification',
                    entity_id=kyc_verification.kyc_id,
                    old_value={'status': 'pending'},
                    new_value={
                        'status': 'approved',
                        'compliance_level': compliance_level,
                        'verified_by': approved_by.email
                    }
                )
                
                # Send approval email
                send_kyc_approved_email(
                    kyc_verification.email,
                    kyc_verification.full_name(),
                    compliance_level
                )
                
                return {
                    'success': True,
                    'kyc_id': kyc_verification.kyc_id,
                    'status': 'approved',
                    'compliance_level': compliance_level,
                    'message': 'KYC verification approved'
                }
        
        except Exception as e:
            logger.error(f"Error approving KYC: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def reject_verification(kyc_verification, rejected_by, reason):
        """Reject KYC verification"""
        try:
            with transaction.atomic():
                # Update verification
                kyc_verification.verification_status = 'rejected'
                kyc_verification.verified_by = rejected_by
                kyc_verification.verified_at = timezone.now()
                kyc_verification.rejection_reason = reason
                kyc_verification.save()
                
                # Log the rejection
                AuditService.log_action(
                    user=rejected_by,
                    action=f'KYC rejected: {kyc_verification.kyc_id}',
                    entity_type='kyc_verification',
                    entity_id=kyc_verification.kyc_id,
                    old_value={'status': 'pending'},
                    new_value={
                        'status': 'rejected',
                        'rejection_reason': reason,
                        'verified_by': rejected_by.email
                    }
                )
                
                # Send rejection email
                send_kyc_rejected_email(
                    kyc_verification.email,
                    kyc_verification.full_name(),
                    reason
                )
                
                return {
                    'success': True,
                    'kyc_id': kyc_verification.kyc_id,
                    'status': 'rejected',
                    'message': 'KYC verification rejected'
                }
        
        except Exception as e:
            logger.error(f"Error rejecting KYC: {str(e)}")
            return {'success': False, 'error': str(e)}


class TACService:
    """Service for TAC operations"""
    
    @staticmethod
    def generate_tac(user, **kwargs):
        """Generate a new TAC"""
        try:
            # Generate TAC code
            tac_code = TACService._generate_tac_code()
            
            # Calculate expiry (5 minutes by default)
            expires_at = timezone.now() + timedelta(minutes=5)
            
            # Create TAC request
            tac_request = TACRequest.objects.create(
                user=user,
                tac_code=tac_code,
                tac_type=kwargs.get('tac_type', 'withdrawal'),
                purpose=kwargs.get('purpose', ''),
                amount=kwargs.get('amount'),
                currency=kwargs.get('currency', 'USD'),
                transaction_id=kwargs.get('transaction_id'),
                sent_via=kwargs.get('sent_via', 'email'),
                sent_to=user.email,
                expires_at=expires_at,
                ip_address=kwargs.get('ip_address'),
                user_agent=kwargs.get('user_agent'),
                compliance_request=kwargs.get('compliance_request')
            )
            
            # Send TAC via email
            send_tac_email(
                user.email,
                tac_code,
                user.get_full_name() or user.username
            )
            
            # Log the generation
            AuditService.log_action(
                user=user,
                action='TAC generated',
                entity_type='tac_request',
                entity_id=tac_request.tac_id,
                new_value={'tac_code': '***', 'expires_at': expires_at}
            )
            
            return {
                'success': True,
                'tac_id': tac_request.tac_id,
                'sent_to': user.email,
                'expires_at': expires_at.isoformat(),
                'time_remaining': 300,  # 5 minutes in seconds
                'message': 'TAC sent successfully'
            }
        
        except Exception as e:
            logger.error(f"Error generating TAC: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def verify_tac(user, tac_code, **kwargs):
        """Verify a TAC"""
        try:
            # Find valid TAC
            tac_request = TACRequest.objects.filter(
                user=user,
                tac_code=tac_code,
                is_used=False,
                is_expired=False,
                expires_at__gt=timezone.now()
            ).first()
            
            if not tac_request:
                # Check for expired or used TAC
                expired_tac = TACRequest.objects.filter(
                    user=user,
                    tac_code=tac_code
                ).first()
                
                if expired_tac:
                    expired_tac.attempts += 1
                    if expired_tac.attempts >= expired_tac.max_attempts:
                        expired_tac.is_expired = True
                    expired_tac.save()
                
                return {
                    'success': False,
                    'error': 'Invalid or expired TAC code'
                }
            
            # Mark TAC as used
            tac_request.is_used = True
            tac_request.used_at = timezone.now()
            tac_request.save()
            
            # Log the verification
            AuditService.log_action(
                user=user,
                action='TAC verified',
                entity_type='tac_request',
                entity_id=tac_request.tac_id,
                new_value={'is_used': True, 'used_at': timezone.now()}
            )
            
            return {
                'success': True,
                'tac_id': tac_request.tac_id,
                'verified_at': tac_request.used_at.isoformat(),
                'message': 'TAC verified successfully'
            }
        
        except Exception as e:
            logger.error(f"Error verifying TAC: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def resend_tac(tac_request):
        """Resend a TAC"""
        try:
            # Check if TAC is still valid
            if not tac_request.is_valid():
                return {
                    'success': False,
                    'error': 'TAC is no longer valid'
                }
            
            # Resend TAC
            send_tac_email(
                tac_request.sent_to,
                tac_request.tac_code,
                tac_request.user.get_full_name() or tac_request.user.username
            )
            
            tac_request.delivery_attempts += 1
            tac_request.save()
            
            # Log the resend
            AuditService.log_action(
                user=tac_request.user,
                action='TAC resent',
                entity_type='tac_request',
                entity_id=tac_request.tac_id,
                new_value={'delivery_attempts': tac_request.delivery_attempts}
            )
            
            return {
                'success': True,
                'tac_id': tac_request.tac_id,
                'sent_to': tac_request.sent_to,
                'expires_at': tac_request.expires_at.isoformat(),
                'message': 'TAC resent successfully'
            }
        
        except Exception as e:
            logger.error(f"Error resending TAC: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _generate_tac_code():
        """Generate a 6-digit TAC code"""
        return ''.join([str(secrets.randbelow(10)) for _ in range(6)])


class VideoCallService:
    """Service for video call operations"""
    
    @staticmethod
    def schedule_call(requested_by, **kwargs):
        """Schedule a video call"""
        try:
            # Get compliance request
            compliance_request = kwargs.get('compliance_request')
            if not compliance_request:
                return {
                    'success': False,
                    'error': 'Compliance request is required'
                }
            
            # Create video call session
            video_call = VideoCallSession.objects.create(
                user=compliance_request.user,
                compliance_request=compliance_request,
                purpose=kwargs.get('purpose', 'KYC Verification'),
                scheduled_for=kwargs.get('scheduled_for'),
                duration_minutes=kwargs.get('duration_minutes', 30),
                agent=kwargs.get('agent'),
                platform=kwargs.get('platform', 'zoom'),
                meeting_link=kwargs.get('meeting_link'),
                meeting_id=kwargs.get('meeting_id'),
                meeting_password=kwargs.get('meeting_password')
            )
            
            # Update compliance request
            compliance_request.video_call_scheduled_at = video_call.scheduled_for
            compliance_request.video_call_link = video_call.meeting_link
            compliance_request.save()
            
            # Send notification emails
            send_video_call_scheduled_email(
                compliance_request.user_email,
                compliance_request.user.get_full_name() or compliance_request.user.email,
                video_call.scheduled_for,
                video_call.meeting_link,
                video_call.meeting_password
            )
            
            # Log the scheduling
            AuditService.log_action(
                user=requested_by,
                action='Video call scheduled',
                entity_type='video_call',
                entity_id=video_call.session_id,
                new_value={
                    'scheduled_for': video_call.scheduled_for,
                    'meeting_link': video_call.meeting_link
                }
            )
            
            return {
                'success': True,
                'session_id': video_call.session_id,
                'scheduled_for': video_call.scheduled_for.isoformat(),
                'meeting_link': video_call.meeting_link,
                'message': 'Video call scheduled successfully'
            }
        
        except Exception as e:
            logger.error(f"Error scheduling video call: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def start_call(video_call):
        """Start a video call"""
        try:
            # Update call status
            video_call.status = 'in_progress'
            video_call.started_at = timezone.now()
            video_call.save()
            
            # Log the start
            AuditService.log_action(
                user=video_call.user,
                action='Video call started',
                entity_type='video_call',
                entity_id=video_call.session_id,
                new_value={'status': 'in_progress', 'started_at': timezone.now()}
            )
            
            return {
                'success': True,
                'session_id': video_call.session_id,
                'status': video_call.status,
                'started_at': video_call.started_at.isoformat(),
                'message': 'Video call started'
            }
        
        except Exception as e:
            logger.error(f"Error starting video call: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def complete_call(video_call, completed_by, verification_passed=False, notes=''):
        """Complete a video call"""
        try:
            # Update call status
            video_call.status = 'completed'
            video_call.ended_at = timezone.now()
            video_call.verification_passed = verification_passed
            video_call.verification_notes = notes
            
            # Calculate duration
            if video_call.started_at:
                duration = (video_call.ended_at - video_call.started_at).total_seconds() / 60
                video_call.actual_duration = int(duration)
            
            video_call.save()
            
            # Update compliance request
            compliance_request = video_call.compliance_request
            compliance_request.video_call_completed_at = timezone.now()
            compliance_request.video_call_notes = notes
            
            if verification_passed:
                compliance_request.status = 'under_review'
            else:
                compliance_request.status = 'info_required'
                compliance_request.review_notes = f"Video call failed: {notes}"
            
            compliance_request.save()
            
            # Log the completion
            AuditService.log_action(
                user=completed_by,
                action='Video call completed',
                entity_type='video_call',
                entity_id=video_call.session_id,
                new_value={
                    'status': 'completed',
                    'verification_passed': verification_passed,
                    'notes': notes
                }
            )
            
            return {
                'success': True,
                'session_id': video_call.session_id,
                'status': video_call.status,
                'verification_passed': verification_passed,
                'message': 'Video call completed'
            }
        
        except Exception as e:
            logger.error(f"Error completing video call: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def reschedule_call(video_call, new_time, rescheduled_by):
        """Reschedule a video call"""
        try:
            # Update call
            video_call.status = 'rescheduled'
            video_call.scheduled_for = new_time
            video_call.save()
            
            # Send reschedule notification
            send_video_call_scheduled_email(
                video_call.user.email,
                video_call.user.get_full_name() or video_call.user.email,
                new_time,
                video_call.meeting_link,
                video_call.meeting_password
            )
            
            # Log the rescheduling
            AuditService.log_action(
                user=rescheduled_by,
                action='Video call rescheduled',
                entity_type='video_call',
                entity_id=video_call.session_id,
                old_value={'scheduled_for': video_call.scheduled_for},
                new_value={'scheduled_for': new_time, 'status': 'rescheduled'}
            )
            
            return {
                'success': True,
                'session_id': video_call.session_id,
                'scheduled_for': new_time.isoformat(),
                'message': 'Video call rescheduled'
            }
        
        except Exception as e:
            logger.error(f"Error rescheduling video call: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def cancel_call(video_call, cancelled_by, reason=''):
        """Cancel a video call"""
        try:
            # Update call
            video_call.status = 'cancelled'
            video_call.save()
            
            # Update compliance request
            compliance_request = video_call.compliance_request
            compliance_request.review_notes = f"Video call cancelled: {reason}"
            compliance_request.save()
            
            # Log the cancellation
            AuditService.log_action(
                user=cancelled_by,
                action='Video call cancelled',
                entity_type='video_call',
                entity_id=video_call.session_id,
                new_value={'status': 'cancelled', 'reason': reason}
            )
            
            return {
                'success': True,
                'session_id': video_call.session_id,
                'status': video_call.status,
                'message': 'Video call cancelled'
            }
        
        except Exception as e:
            logger.error(f"Error cancelling video call: {str(e)}")
            return {'success': False, 'error': str(e)}


class DocumentService:
    """Service for document operations"""
    
    @staticmethod
    def save_document(file, user_id, doc_type):
        """Save uploaded document and return metadata"""
        try:
            # Create secure directory structure
            timestamp = int(timezone.now().timestamp())
            safe_user_id = str(user_id).replace('/', '_').replace('\\', '_')
            safe_doc_type = str(doc_type).replace('/', '_').replace('\\', '_')
            
            # Create directory
            user_dir = f"compliance/documents/{safe_user_id}/{timestamp}"
            os.makedirs(os.path.join(settings.MEDIA_ROOT, user_dir), exist_ok=True)
            
            # Generate secure filename
            file_extension = os.path.splitext(file.name)[1].lower()
            if not file_extension:
                content_type = file.content_type
                file_extension = mimetypes.guess_extension(content_type) or '.bin'
            
            unique_id = secrets.token_hex(8)
            safe_filename = f"{safe_doc_type}_{unique_id}{file_extension}"
            file_path = os.path.join(user_dir, safe_filename)
            
            # Save file
            saved_path = default_storage.save(file_path, ContentFile(file.read()))
            
            # Get full path for hashing
            if hasattr(default_storage, 'path'):
                full_path = default_storage.path(saved_path)
            else:
                full_path = os.path.join(settings.MEDIA_ROOT, saved_path)
            
            # Calculate file hash
            file_hash = DocumentService._hash_file(full_path)
            file_size = file.size
            
            logger.info(f"Document saved: {saved_path}, size: {file_size} bytes")
            
            return saved_path, file_hash, file_size
        
        except Exception as e:
            logger.error(f"Error saving document: {e}")
            raise
    
    @staticmethod
    def _hash_file(file_path):
        """Generate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error hashing file {file_path}: {e}")
            return None


class AuditService:
    """Service for audit logging"""
    
    @staticmethod
    def log_action(user, action, entity_type, entity_id, old_value=None, new_value=None, **kwargs):
        """Log an action to audit trail"""
        try:
            audit_log = ComplianceAuditLog.objects.create(
                user=user,
                user_email=user.email if user else None,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                old_value=old_value,
                new_value=new_value,
                ip_address=kwargs.get('ip_address'),
                user_agent=kwargs.get('user_agent'),
                location=kwargs.get('location')
            )
            
            logger.info(f"Audit log created: {action} for {entity_type} {entity_id}")
            return audit_log
        
        except Exception as e:
            logger.error(f"Error creating audit log: {e}")
            return None


class AlertService:
    """Service for compliance alerts"""
    
    @staticmethod
    def create_alert(alert_type, severity, title, description, **kwargs):
        """Create a compliance alert"""
        try:
            alert = ComplianceAlert.objects.create(
                alert_type=alert_type,
                severity=severity,
                title=title,
                description=description,
                compliance_request=kwargs.get('compliance_request'),
                kyc_verification=kwargs.get('kyc_verification'),
                user=kwargs.get('user'),
                alert_data=kwargs.get('alert_data', {}),
                trigger_conditions=kwargs.get('trigger_conditions', {}),
                expires_at=timezone.now() + timedelta(hours=24)
            )
            
            logger.info(f"Alert created: {alert_type} - {title}")
            return alert
        
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            return None
    
    @staticmethod
    def cleanup_expired_alerts():
        """Clean up expired alerts"""
        try:
            expired_count = ComplianceAlert.objects.filter(
                expires_at__lt=timezone.now(),
                is_resolved=False
            ).update(is_resolved=True)
            
            logger.info(f"Cleaned up {expired_count} expired alerts")
            return expired_count
        
        except Exception as e:
            logger.error(f"Error cleaning up alerts: {e}")
            return 0


class ScheduledTasksService:
    """Service for scheduled compliance tasks"""
    
    @staticmethod
    def cleanup_expired_tacs():
        """Clean up expired TAC codes"""
        try:
            expired_count = TACRequest.objects.filter(
                expires_at__lt=timezone.now(),
                is_used=False,
                is_expired=False
            ).update(is_expired=True)
            
            logger.info(f"Cleaned up {expired_count} expired TAC codes")
            return expired_count
        
        except Exception as e:
            logger.error(f"Error cleaning up TAC codes: {e}")
            return 0
    
    @staticmethod
    def check_kyc_expirations():
        """Check for expiring KYC verifications"""
        try:
            expiry_threshold = timezone.now() + timedelta(days=30)
            expiring_kyc = KYCVerification.objects.filter(
                next_review_date__lte=expiry_threshold,
                verification_status='approved'
            )
            
            for kyc in expiring_kyc:
                AlertService.create_alert(
                    alert_type='kyc_expiring',
                    severity='warning',
                    title=f"KYC expiring soon: {kyc.kyc_id}",
                    description=f"KYC for {kyc.full_name()} expires on {kyc.next_review_date.date()}",
                    kyc_verification=kyc,
                    user=kyc.user
                )
            
            logger.info(f"Checked {expiring_kyc.count()} expiring KYC verifications")
            return expiring_kyc.count()
        
        except Exception as e:
            logger.error(f"Error checking KYC expirations: {e}")
            return 0
    
    @staticmethod
    def generate_daily_stats():
        """Generate daily compliance statistics"""
        try:
            today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            yesterday_start = today_start - timedelta(days=1)
            
            # Calculate stats
            stats = {
                'period_type': 'daily',
                'period_start': yesterday_start,
                'period_end': today_start,
                'total_requests': ComplianceRequest.objects.filter(
                    created_at__range=[yesterday_start, today_start]
                ).count(),
                'approved_requests': ComplianceRequest.objects.filter(
                    created_at__range=[yesterday_start, today_start],
                    status='approved'
                ).count(),
                'pending_requests': ComplianceRequest.objects.filter(
                    created_at__range=[yesterday_start, today_start],
                    status='pending'
                ).count(),
                'kyc_submissions': KYCVerification.objects.filter(
                    created_at__range=[yesterday_start, today_start]
                ).count(),
                'kyc_approved': KYCVerification.objects.filter(
                    created_at__range=[yesterday_start, today_start],
                    verification_status='approved'
                ).count(),
                'tac_generated': TACRequest.objects.filter(
                    created_at__range=[yesterday_start, today_start]
                ).count(),
                'tac_verified': TACRequest.objects.filter(
                    created_at__range=[yesterday_start, today_start],
                    is_used=True
                ).count(),
            }
            
            logger.info(f"Generated daily stats: {stats}")
            return stats
        
        except Exception as e:
            logger.error(f"Error generating daily stats: {e}")
            return {}