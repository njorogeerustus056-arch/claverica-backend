"""
compliance/services.py - Business logic and services for central compliance app
"""

import secrets
import hashlib
import os
import mimetypes
import json
from datetime import timedelta, datetime
from typing import Dict, List, Optional, Tuple, Any, Union
from django.utils import timezone
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.db import transaction, models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
import logging

from .models import (
    ComplianceRequest, KYCVerification, KYCDocument,
    TACRequest, VideoCallSession, ComplianceAuditLog,
    ComplianceAlert, ComplianceRule, ComplianceProfile
)
from .email_service import (
    send_tac_email, send_kyc_approved_email,
    send_kyc_rejected_email, send_video_call_scheduled_email,
    send_compliance_decision_email, send_compliance_escalation_email
)

logger = logging.getLogger(__name__)


class BaseService:
    """Base service class with common utilities"""
    
    @staticmethod
    def handle_exception(method_name: str, e: Exception, user: Optional['User'] = None) -> Dict[str, Any]:
        """Standard exception handler for all services"""
        error_msg = f"Error in {method_name}: {str(e)}"
        user_email = user.email if user and hasattr(user, 'email') else None
        logger.error(error_msg, exc_info=True, extra={'user': user_email})
        return {
            'success': False, 
            'error': 'An internal error occurred. Please try again later.',
            'error_code': 'SERVICE_ERROR',
            'error_details': str(e) if settings.DEBUG else None
        }
    
    @staticmethod
    def validate_required_fields(data: Dict, required_fields: List[str]) -> Tuple[bool, str]:
        """Validate required fields in data dictionary"""
        missing_fields = []
        for field in required_fields:
            if field not in data or data[field] in (None, '', []):
                missing_fields.append(field)
        
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"
        return True, ""
    
    @staticmethod
    def sanitize_input(value: Any) -> Any:
        """Sanitize input to prevent injection attacks"""
        if isinstance(value, str):
            # Remove potentially dangerous characters
            import re
            value = re.sub(r'[<>"\']', '', value)
            value = value.strip()
        return value


class ComplianceService:
    """Service for compliance request operations"""
    
    @staticmethod
    def create_request(user: 'User', app_name: str, request_type: str, **kwargs) -> Dict[str, Any]:
        """Create a new compliance request"""
        try:
            # Validate user
            if not user or not isinstance(user, User):
                return {'success': False, 'error': 'Valid user required'}
            
            if not user.email:
                return {'success': False, 'error': 'User email is required'}
            
            with transaction.atomic():
                # Sanitize and validate input data
                sanitized_data = {}
                for key, value in kwargs.items():
                    if isinstance(value, str):
                        sanitized_data[key] = BaseService.sanitize_input(value)
                    else:
                        sanitized_data[key] = value
                
                # Prepare request data with default values
                request_data = {
                    'user': user,
                    'app_name': app_name,
                    'request_type': request_type,
                    'user_email': user.email,
                    'user_phone': sanitized_data.get('user_phone', ''),
                    'amount': sanitized_data.get('amount'),
                    'currency': sanitized_data.get('currency', 'USD'),
                    'description': sanitized_data.get('description', ''),
                    'form_data': sanitized_data.get('form_data', {}),
                    'documents': sanitized_data.get('documents', []),
                    'metadata': sanitized_data.get('metadata', {}),
                    'ip_address': sanitized_data.get('ip_address'),
                    'user_agent': sanitized_data.get('user_agent'),
                    'device_id': sanitized_data.get('device_id'),
                    'location_data': sanitized_data.get('location_data'),
                    'external_reference': sanitized_data.get('external_reference'),
                    'created_by': user,
                    'updated_by': user,
                }
                
                # Validate amount if provided
                if request_data['amount'] is not None:
                    try:
                        amount = float(request_data['amount'])
                        if amount < 0:
                            return {'success': False, 'error': 'Amount cannot be negative'}
                        request_data['amount'] = amount
                    except (ValueError, TypeError):
                        return {'success': False, 'error': 'Invalid amount format'}
                
                # Create compliance request
                compliance_request = ComplianceRequest.objects.create(**request_data)
                
                # Run risk assessment
                risk_score, risk_level = ComplianceService.assess_risk(compliance_request)
                
                # Apply compliance rules
                rules_applied = ComplianceService.apply_compliance_rules(compliance_request)
                
                # Create compliance profile if needed
                if not hasattr(user, 'compliance_profile'):
                    ComplianceService._create_compliance_profile(user)
                
                # Update user compliance profile
                ComplianceService._update_compliance_profile(user, compliance_request, risk_level)
                
                # Log the creation
                AuditService.log_action(
                    user=user,
                    action=f"Compliance request created: {request_type}",
                    entity_type='compliance_request',
                    entity_id=compliance_request.compliance_id,
                    new_value={
                        'status': compliance_request.status,
                        'risk_level': risk_level,
                        'risk_score': risk_score,
                        'rules_applied': rules_applied
                    },
                    ip_address=sanitized_data.get('ip_address'),
                    user_agent=sanitized_data.get('user_agent')
                )
                
                # Create alerts based on risk level
                ComplianceService._create_risk_alerts(compliance_request, user)
                
                return {
                    'success': True,
                    'compliance_id': compliance_request.compliance_id,
                    'status': compliance_request.status,
                    'risk_level': risk_level,
                    'risk_score': risk_score,
                    'requires_manual_review': compliance_request.requires_manual_review,
                    'requires_tac': compliance_request.requires_tac,
                    'requires_video_call': compliance_request.requires_video_call,
                    'priority': compliance_request.priority,
                    'rules_applied': rules_applied,
                    'created_at': compliance_request.created_at.isoformat(),
                    'message': 'Compliance request created successfully'
                }
        
        except Exception as e:
            return BaseService.handle_exception('create_request', e, user)
    
    @staticmethod
    def assess_risk(compliance_request: ComplianceRequest) -> Tuple[int, str]:
        """Assess risk for a compliance request with enhanced scoring"""
        try:
            risk_score = 0
            risk_factors = []
            
            # Amount-based risk
            if compliance_request.amount:
                if compliance_request.amount > 10000:
                    risk_score += 50
                    risk_factors.append('high_amount')
                elif compliance_request.amount > 5000:
                    risk_score += 30
                    risk_factors.append('medium_amount')
                elif compliance_request.amount > 1000:
                    risk_score += 15
                    risk_factors.append('low_amount')
            
            # User history risk
            user_risk_score = ComplianceService._calculate_user_risk(compliance_request.user)
            risk_score += user_risk_score['score']
            risk_factors.extend(user_risk_score['factors'])
            
            # Time-based risk (unusual hours)
            hour = compliance_request.created_at.hour
            if hour < 6 or hour > 22:  # Outside business hours (6 AM - 10 PM)
                risk_score += 10
                risk_factors.append('unusual_hours')
            
            # Geographic risk
            location_data = compliance_request.metadata.get('location_data', {})
            if location_data:
                country_risk = ComplianceService._get_country_risk(location_data.get('country'))
                risk_score += country_risk['score']
                risk_factors.extend(country_risk['factors'])
            
            # Device and IP risk
#             device_risk = ComplianceService._assess_device_risk(
#                 None,  # device_id not available
#                 compliance_request.ip_address,
#                 compliance_request.user
#             )
#             risk_score += device_risk['score']
#             risk_factors.extend(device_risk['factors'])
            
            # Determine risk level and requirements
            risk_assessment = ComplianceService._determine_risk_level(
                risk_score, risk_factors, compliance_request.amount
            )
            
            # Update the request
            compliance_request.risk_score = risk_score
            compliance_request.risk_level = risk_assessment['risk_level']
            compliance_request.risk_factors = risk_factors
            compliance_request.requires_manual_review = risk_assessment['requires_manual_review']
            compliance_request.requires_video_call = risk_assessment['requires_video_call']
            compliance_request.requires_tac = risk_assessment['requires_tac']
            compliance_request.priority = 'high' if risk_assessment['risk_level'] == 'high' else 'normal'
            compliance_request.save()
            
            return {
                'risk_score': risk_score,
                'risk_level': risk_assessment['risk_level'],
                'requires_tac': risk_assessment.get('requires_tac', False),
                'requires_video_call': risk_assessment.get('requires_video_call', False),
                'requires_manual_review': risk_assessment.get('requires_manual_review', False),
                'priority': risk_assessment.get('priority', 'normal')
            }
        
        except Exception as e:
            if isinstance(e, AttributeError) and "device_id" in str(e):
                logger.debug(f"Expected missing device_id field: {str(e)}")
            else:
                logger.error(f"Error assessing risk: {str(e)}", exc_info=True)
            return {'risk_score': 0, 'risk_level': 'low', 'requires_tac': False, 'requires_video_call': False, 'requires_manual_review': False, 'priority': 'normal'}
    
    @staticmethod
    def _calculate_user_risk(user: 'User') -> Dict[str, Any]:
        """Calculate risk based on user history"""
        score = 0
        factors = []
        
        try:
            # Recent requests count
            recent_requests = ComplianceRequest.objects.filter(
                user=user,
                created_at__gte=timezone.now() - timedelta(days=30)
            ).count()
            
            if recent_requests > 10:
                score += 20
                factors.append('high_frequency')
            elif recent_requests > 5:
                score += 10
                factors.append('medium_frequency')
            
            # Previous rejections
            recent_rejections = ComplianceRequest.objects.filter(
                user=user,
                status='rejected',
                created_at__gte=timezone.now() - timedelta(days=90)
            ).count()
            
            if recent_rejections > 2:
                score += 30
                factors.append('multiple_rejections')
            elif recent_rejections > 0:
                score += 15
                factors.append('previous_rejection')
            
        except Exception as e:
            logger.error(f"Error calculating user risk: {e}")
        
        return {'score': score, 'factors': factors}
    
    @staticmethod
    def _get_country_risk(country_code: Optional[str]) -> Dict[str, Any]:
        """Get risk score for a country"""
        high_risk_countries = getattr(settings, 'HIGH_RISK_COUNTRIES', ['AF', 'IR', 'KP', 'SY', 'YE'])
        medium_risk_countries = getattr(settings, 'MEDIUM_RISK_COUNTRIES', ['RU', 'CN', 'PK', 'NG'])
        
        score = 0
        factors = []
        
        if not country_code:
            return {'score': score, 'factors': factors}
        
        country_code = country_code.upper()
        
        if country_code in high_risk_countries:
            score += 40
            factors.append('high_risk_country')
        elif country_code in medium_risk_countries:
            score += 20
            factors.append('medium_risk_country')
        
        return {'score': score, 'factors': factors}
    
    @staticmethod
    def _assess_device_risk(device_id: Optional[str], ip_address: Optional[str], user: 'User') -> Dict[str, Any]:
        """Assess risk based on device and IP"""
        score = 0
        factors = []
        
        if device_id:
            try:
                # Check device history
                device_requests = ComplianceRequest.objects.filter(
                    device_id=device_id
                ).exclude(user=user).count()
                
                if device_requests > 0:
                    score += 25
                    factors.append('shared_device')
            except Exception as e:
                logger.error(f"Error assessing device risk: {e}")
        
        # IP risk (simplified - would use IP intelligence service)
        if ip_address:
            # Check if IP is from VPN/Proxy or suspicious
            if ComplianceService._is_suspicious_ip(ip_address):
                score += 30
                factors.append('suspicious_ip')
        
        return {'score': score, 'factors': factors}
    
    @staticmethod
    def _is_suspicious_ip(ip_address: str) -> bool:
        """Check if IP is suspicious (simplified)"""
        # This would integrate with an IP intelligence service
        # For now, check for known VPN ranges or private IPs
        suspicious_prefixes = ['192.168.', '10.', '172.16.', '172.17.', '172.18.', 
                              '172.19.', '172.20.', '172.21.', '172.22.', '172.23.',
                              '172.24.', '172.25.', '172.26.', '172.27.', '172.28.',
                              '172.29.', '172.30.', '172.31.']
        
        # Also check for localhost
        if ip_address == '127.0.0.1' or ip_address == '::1':
            return True
        
        return any(ip_address.startswith(prefix) for prefix in suspicious_prefixes)
    
    @staticmethod
    def _determine_risk_level(risk_score: int, risk_factors: List[str], amount: Optional[float] = None) -> Dict[str, Any]:
        """Determine risk level and requirements"""
        if risk_score >= 70:
            risk_level = 'high'
            requires_manual_review = True
            requires_video_call = True
            requires_tac = True if amount and amount > 500 else False
        elif risk_score >= 40:
            risk_level = 'medium'
            requires_manual_review = True
            requires_video_call = 'high_risk_country' in risk_factors
            requires_tac = True if amount and amount > 1000 else False
        else:
            risk_level = 'low'
            requires_manual_review = False
            requires_video_call = False
            requires_tac = True if amount and amount > 5000 else False
        
        return {
            'risk_level': risk_level,
            'requires_manual_review': requires_manual_review,
            'requires_video_call': requires_video_call,
            'requires_tac': requires_tac
        }
    
    @staticmethod
    def _create_compliance_profile(user: 'User'):
        """Create a compliance profile for user"""
        try:
            ComplianceProfile.objects.create(
                user=user,
                email=user.email,
                risk_level='low',
                compliance_status='pending'
            )
            logger.info(f"Created compliance profile for user: {user.email}")
        except Exception as e:
            logger.error(f"Error creating compliance profile: {str(e)}", exc_info=True)
    
    @staticmethod
    def _update_compliance_profile(user: 'User', compliance_request: ComplianceRequest, risk_level: str):
        """Update user compliance profile"""
        try:
            profile, created = ComplianceProfile.objects.get_or_create(user=user)
            
            # Update risk level if higher
            risk_levels = {'low': 1, 'medium': 2, 'high': 3}
            current_level = risk_levels.get(profile.risk_level, 0)
            new_level = risk_levels.get(risk_level, 0)
            
            if new_level > current_level:
                profile.risk_level = risk_level
            
            # Update request count
            profile.total_requests += 1
            profile.last_request_date = timezone.now()
            profile.save()
            
        except Exception as e:
            logger.error(f"Error updating compliance profile: {str(e)}", exc_info=True)
    
    @staticmethod
    def _create_risk_alerts(compliance_request: ComplianceRequest, user: 'User'):
        """Create alerts based on risk assessment"""
        try:
            if compliance_request.risk_level == 'high':
                AlertService.create_alert(
                    alert_type='risk_threshold',
                    severity='critical',
                    title=f"High risk compliance request: {compliance_request.compliance_id}",
                    description=f"New {compliance_request.request_type} request from {user.email} flagged as high risk",
                    compliance_request=compliance_request,
                    user=user,
                    alert_data={
                        'risk_score': compliance_request.risk_score,
                        'risk_factors': compliance_request.risk_factors,
                        'amount': compliance_request.amount
                    }
                )
            
            if 'shared_device' in compliance_request.risk_factors:
                AlertService.create_alert(
                    alert_type='suspicious_device',
                    severity='warning',
                    title=f"Suspicious device detected: {compliance_request.compliance_id}",
                    description=f"Request from device used by multiple users",
                    compliance_request=compliance_request,
                    user=user
                )
        
        except Exception as e:
            logger.error(f"Error creating risk alerts: {str(e)}", exc_info=True)
    
    @staticmethod
    def apply_compliance_rules(compliance_request: ComplianceRequest) -> List[str]:
        """Apply compliance rules to request"""
        applied_rules = []
        try:
            # Get active rules for this app and request type
            rules = ComplianceRule.objects.filter(
                is_active=True,
                rule_type=compliance_request.request_type,
                applicable_apps__in=['all', compliance_request.app_name]
            )
            
            for rule in rules:
                if ComplianceService._evaluate_rule(rule, compliance_request):
                    # Apply rule action
                    ComplianceService._apply_rule_action(rule, compliance_request)
                    applied_rules.append(rule.rule_name)
                    
                    # Log rule application
                    AuditService.log_action(
                        user=compliance_request.user,
                        action=f"Compliance rule applied: {rule.rule_name}",
                        entity_type='compliance_request',
                        entity_id=compliance_request.compliance_id,
                        new_value={
                            'rule_name': rule.rule_name,
                            'action_taken': rule.action_taken
                        }
                    )
            
            compliance_request.rules_applied = applied_rules
            compliance_request.save()
            
        except Exception as e:
            logger.error(f"Error applying compliance rules: {str(e)}", exc_info=True)
        
        return applied_rules
    
    @staticmethod
    def _evaluate_rule(rule: ComplianceRule, compliance_request: ComplianceRequest) -> bool:
        """Evaluate if a rule applies to the request"""
        try:
            # Check amount threshold
            if rule.threshold_amount and compliance_request.amount:
                if rule.condition_operator == 'greater_than' and compliance_request.amount > rule.threshold_amount:
                    return True
                elif rule.condition_operator == 'less_than' and compliance_request.amount < rule.threshold_amount:
                    return True
                elif rule.condition_operator == 'equals' and compliance_request.amount == rule.threshold_amount:
                    return True
            
            # Check country restrictions
            if rule.restricted_countries:
                try:
                    restricted = json.loads(rule.restricted_countries)
                    location_data = compliance_request.metadata.get('location_data', {})
                    country = location_data.get('country', '')
                    if country and country in restricted:
                        return True
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing restricted_countries JSON: {e}")
            
            # Check user risk level
            if rule.user_risk_level:
                user_profile = getattr(compliance_request.user, 'compliance_profile', None)
                if user_profile and user_profile.risk_level in rule.user_risk_level:
                    return True
            
            # Check request type
            if rule.rule_type and rule.rule_type != compliance_request.request_type:
                return False
            
            return False
        
        except Exception as e:
            logger.error(f"Error evaluating rule: {str(e)}", exc_info=True)
            return False
    
    @staticmethod
    def _apply_rule_action(rule: ComplianceRule, compliance_request: ComplianceRequest):
        """Apply action based on rule"""
        if rule.action_taken == 'flag_for_review':
            compliance_request.requires_manual_review = True
            compliance_request.priority = 'high'
        elif rule.action_taken == 'require_tac':
            compliance_request.requires_tac = True
        elif rule.action_taken == 'require_video_call':
            compliance_request.requires_video_call = True
        elif rule.action_taken == 'auto_reject':
            compliance_request.status = 'rejected'
            compliance_request.decision = 'reject'
            compliance_request.decision_reason = f"Auto-rejected by rule: {rule.rule_name}"
        elif rule.action_taken == 'auto_approve':
            compliance_request.status = 'approved'
            compliance_request.decision = 'approve'
            compliance_request.decision_notes = f"Auto-approved by rule: {rule.rule_name}"
        
        compliance_request.save()
    
    @staticmethod
    def approve_request(compliance_request: ComplianceRequest, approved_by: 'User', notes: str = '') -> Dict[str, Any]:
        """Approve a compliance request"""
        try:
            with transaction.atomic():
                # Validate request can be approved
                if compliance_request.status not in ['pending', 'under_review', 'info_required']:
                    return {
                        'success': False,
                        'error': f'Request cannot be approved in current status: {compliance_request.status}'
                    }
                
                # Update request status
                old_status = compliance_request.status
                compliance_request.status = 'approved'
                compliance_request.decision = 'approve'
                compliance_request.reviewed_by = approved_by
                compliance_request.reviewed_at = timezone.now()
                compliance_request.resolved_at = timezone.now()
                compliance_request.decision_notes = notes
                compliance_request.save()
                
                # Update user compliance profile
                profile = getattr(compliance_request.user, 'compliance_profile', None)
                if profile:
                    profile.approved_requests += 1
                    profile.last_approved_date = timezone.now()
                    profile.compliance_status = 'verified'
                    profile.save()
                
                # Log the approval
                AuditService.log_action(
                    user=approved_by,
                    action=f"Compliance request approved: {compliance_request.compliance_id}",
                    entity_type='compliance_request',
                    entity_id=compliance_request.compliance_id,
                    old_value={'status': old_status},
                    new_value={
                        'status': 'approved',
                        'reviewed_by': approved_by.email,
                        'reviewed_at': timezone.now().isoformat(),
                        'decision_notes': notes
                    }
                )
                
                # Send notification to user
                user_name = compliance_request.user.get_full_name() or compliance_request.user.email
                send_compliance_decision_email(
                    to_email=compliance_request.user_email,
                    user_name=user_name,
                    request_type=compliance_request.request_type,
                    decision='approved',
                    notes=notes,
                    compliance_id=compliance_request.compliance_id,
                    additional_data={
                        'amount': compliance_request.amount,
                        'currency': compliance_request.currency,
                        'reference_number': compliance_request.compliance_id
                    }
                )
                
                return {
                    'success': True,
                    'message': 'Compliance request approved',
                    'compliance_id': compliance_request.compliance_id,
                    'status': compliance_request.status,
                    'reviewed_at': compliance_request.reviewed_at.isoformat(),
                    'reviewed_by': approved_by.email
                }
        
        except Exception as e:
            return BaseService.handle_exception('approve_request', e, approved_by)
    
    @staticmethod
    def reject_request(compliance_request: ComplianceRequest, rejected_by: 'User', reason: str, notes: str = '') -> Dict[str, Any]:
        """Reject a compliance request"""
        try:
            with transaction.atomic():
                # Validate request can be rejected
                if compliance_request.status not in ['pending', 'under_review', 'info_required']:
                    return {
                        'success': False,
                        'error': f'Request cannot be rejected in current status: {compliance_request.status}'
                    }
                
                # Update request status
                old_status = compliance_request.status
                compliance_request.status = 'rejected'
                compliance_request.decision = 'reject'
                compliance_request.reviewed_by = rejected_by
                compliance_request.reviewed_at = timezone.now()
                compliance_request.resolved_at = timezone.now()
                compliance_request.decision_reason = reason
                compliance_request.decision_notes = notes
                compliance_request.save()
                
                # Update user compliance profile
                profile = getattr(compliance_request.user, 'compliance_profile', None)
                if profile:
                    profile.rejected_requests += 1
                    profile.last_rejected_date = timezone.now()
                    if profile.rejected_requests > 3:
                        profile.risk_level = 'high'
                    profile.save()
                
                # Log the rejection
                AuditService.log_action(
                    user=rejected_by,
                    action=f"Compliance request rejected: {compliance_request.compliance_id}",
                    entity_type='compliance_request',
                    entity_id=compliance_request.compliance_id,
                    old_value={'status': old_status},
                    new_value={
                        'status': 'rejected',
                        'reviewed_by': rejected_by.email,
                        'reviewed_at': timezone.now().isoformat(),
                        'reason': reason,
                        'notes': notes
                    }
                )
                
                # Send notification to user
                user_name = compliance_request.user.get_full_name() or compliance_request.user.email
                send_compliance_decision_email(
                    to_email=compliance_request.user_email,
                    user_name=user_name,
                    request_type=compliance_request.request_type,
                    decision='rejected',
                    notes=f"{reason}. {notes}",
                    compliance_id=compliance_request.compliance_id,
                    additional_data={
                        'amount': compliance_request.amount,
                        'currency': compliance_request.currency
                    }
                )
                
                # Create alert for pattern detection
                AlertService.create_alert(
                    alert_type='rejection_pattern',
                    severity='warning',
                    title=f"Compliance request rejected: {compliance_request.compliance_id}",
                    description=f"Request from {compliance_request.user.email} rejected. Reason: {reason}",
                    compliance_request=compliance_request,
                    user=rejected_by
                )
                
                return {
                    'success': True,
                    'message': 'Compliance request rejected',
                    'compliance_id': compliance_request.compliance_id,
                    'status': compliance_request.status,
                    'reviewed_at': compliance_request.reviewed_at.isoformat(),
                    'reviewed_by': rejected_by.email
                }
        
        except Exception as e:
            return BaseService.handle_exception('reject_request', e, rejected_by)
    
    @staticmethod
    def escalate_request(compliance_request: ComplianceRequest, escalated_by: 'User', reason: str) -> Dict[str, Any]:
        """Escalate a compliance request"""
        try:
            # Update request
            old_status = compliance_request.status
            compliance_request.status = 'under_review'
            compliance_request.priority = 'high'
            compliance_request.escalated_by = escalated_by
            compliance_request.escalated_at = timezone.now()
            compliance_request.escalation_reason = reason
            compliance_request.save()
            
            # Create alert for managers
            AlertService.create_alert(
                alert_type='escalation',
                severity='critical',
                title=f"Compliance request escalated: {compliance_request.compliance_id}",
                description=f"Request escalated by {escalated_by.email}. Reason: {reason}",
                compliance_request=compliance_request,
                user=escalated_by,
                alert_data={
                    'old_status': old_status,
                    'escalation_reason': reason,
                    'risk_level': compliance_request.risk_level
                }
            )
            
            # Send escalation email to managers
            send_compliance_escalation_email(
                compliance_request,
                escalated_by,
                reason
            )
            
            # Log the escalation
            AuditService.log_action(
                user=escalated_by,
                action=f"Compliance request escalated: {compliance_request.compliance_id}",
                entity_type='compliance_request',
                entity_id=compliance_request.compliance_id,
                old_value={'status': old_status, 'priority': compliance_request.priority},
                new_value={
                    'status': 'under_review',
                    'priority': 'high',
                    'escalation_reason': reason,
                    'escalated_by': escalated_by.email
                }
            )
            
            return {
                'success': True,
                'message': 'Request escalated successfully',
                'compliance_id': compliance_request.compliance_id,
                'status': compliance_request.status,
                'priority': compliance_request.priority,
                'escalated_by': escalated_by.email,
                'escalated_at': compliance_request.escalated_at.isoformat()
            }
        
        except Exception as e:
            return BaseService.handle_exception('escalate_request', e, escalated_by)
    
    @staticmethod
    def request_additional_info(compliance_request: ComplianceRequest, requested_by: 'User', info_required: str) -> Dict[str, Any]:
        """Request additional information for a compliance request"""
        try:
            # Update request
            old_status = compliance_request.status
            compliance_request.status = 'info_required'
            compliance_request.review_notes = info_required
            compliance_request.info_requested_by = requested_by
            compliance_request.info_requested_at = timezone.now()
            compliance_request.save()
            
            # Create alert for user
            AlertService.create_alert(
                alert_type='info_required',
                severity='info',
                title=f"Additional information required: {compliance_request.compliance_id}",
                description=info_required,
                compliance_request=compliance_request,
                user=compliance_request.user,
                alert_data={
                    'deadline': (timezone.now() + timedelta(days=3)).isoformat(),
                    'requested_by': requested_by.email
                }
            )
            
            # Log the request
            AuditService.log_action(
                user=requested_by,
                action=f"Additional info requested: {compliance_request.compliance_id}",
                entity_type='compliance_request',
                entity_id=compliance_request.compliance_id,
                old_value={'status': old_status},
                new_value={
                    'status': 'info_required',
                    'info_required': info_required,
                    'requested_by': requested_by.email,
                    'requested_at': timezone.now().isoformat()
                }
            )
            
            return {
                'success': True,
                'message': 'Additional information requested',
                'compliance_id': compliance_request.compliance_id,
                'status': compliance_request.status,
                'info_requested_at': compliance_request.info_requested_at.isoformat(),
                'info_requested_by': requested_by.email
            }
        
        except Exception as e:
            return BaseService.handle_exception('request_additional_info', e, requested_by)
    
    @staticmethod
    def update_request_status(compliance_request: ComplianceRequest, new_status: str, updated_by: 'User', notes: str = '') -> Dict[str, Any]:
        """Update compliance request status"""
        try:
            valid_transitions = {
                'pending': ['under_review', 'info_required', 'approved', 'rejected'],
                'under_review': ['info_required', 'approved', 'rejected'],
                'info_required': ['under_review', 'approved', 'rejected'],
            }
            
            if new_status not in valid_transitions.get(compliance_request.status, []):
                return {
                    'success': False,
                    'error': f'Invalid status transition from {compliance_request.status} to {new_status}'
                }
            
            old_status = compliance_request.status
            compliance_request.status = new_status
            if notes:
                compliance_request.decision_notes = notes
            compliance_request.save()
            
            # Log the status change
            AuditService.log_action(
                user=updated_by,
                action=f"Request status updated: {old_status} -> {new_status}",
                entity_type='compliance_request',
                entity_id=compliance_request.compliance_id,
                old_value={'status': old_status},
                new_value={
                    'status': new_status, 
                    'updated_by': updated_by.email,
                    'updated_at': timezone.now().isoformat(),
                    'notes': notes
                }
            )
            
            return {
                'success': True,
                'message': f'Request status updated to {new_status}',
                'compliance_id': compliance_request.compliance_id,
                'old_status': old_status,
                'new_status': new_status,
                'updated_by': updated_by.email,
                'updated_at': timezone.now().isoformat()
            }
        
        except Exception as e:
            return BaseService.handle_exception('update_request_status', e, updated_by)


class KYCService(BaseService):
    """Service for KYC verification operations"""
    
    @staticmethod
    def create_verification(user: 'User', form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new KYC verification"""
        try:
            # Validate required fields
            required_fields = ['first_name', 'last_name', 'date_of_birth', 
                             'nationality', 'country_of_residence', 'id_number']
            valid, error_msg = BaseService.validate_required_fields(form_data, required_fields)
            if not valid:
                return {'success': False, 'error': error_msg}
            
            with transaction.atomic():
                # Check for existing KYC
                existing_kyc = KYCVerification.objects.filter(
                    user=user,
                    verification_status__in=['pending', 'approved', 'pending_review', 'pending_final_review']
                ).exists()
                
                if existing_kyc:
                    return {
                        'success': False,
                        'error': 'User already has an active KYC verification'
                    }
                
                # Sanitize form data
                sanitized_data = {}
                for key, value in form_data.items():
                    if isinstance(value, str):
                        sanitized_data[key] = BaseService.sanitize_input(value)
                    else:
                        sanitized_data[key] = value
                
                # Validate date_of_birth
                date_of_birth = sanitized_data.get('date_of_birth')
                if date_of_birth:
                    if isinstance(date_of_birth, str):
                        try:
                            datetime.strptime(date_of_birth, '%Y-%m-%d')
                        except ValueError:
                            return {'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD'}
                
                # Create KYC verification
                kyc_data = {
                    'user': user,
                    'first_name': sanitized_data.get('first_name'),
                    'last_name': sanitized_data.get('last_name'),
                    'date_of_birth': sanitized_data.get('date_of_birth'),
                    'nationality': sanitized_data.get('nationality'),
                    'country_of_residence': sanitized_data.get('country_of_residence'),
                    'email': sanitized_data.get('email', user.email),
                    'phone_number': sanitized_data.get('phone_number'),
                    'address_line1': sanitized_data.get('address_line1'),
                    'address_line2': sanitized_data.get('address_line2'),
                    'city': sanitized_data.get('city'),
                    'state': sanitized_data.get('state'),
                    'postal_code': sanitized_data.get('postal_code'),
                    'country': sanitized_data.get('country'),
                    'id_number': sanitized_data.get('id_number'),
                    'id_type': sanitized_data.get('id_type'),
                    'occupation': sanitized_data.get('occupation'),
                    'employment_status': sanitized_data.get('employment_status'),
                    'employer_name': sanitized_data.get('employer_name'),
                    'annual_income': sanitized_data.get('annual_income'),
                    'source_of_funds': sanitized_data.get('source_of_funds'),
                    'purpose_of_account': sanitized_data.get('purpose_of_account'),
                    'expected_monthly_volume': sanitized_data.get('expected_monthly_volume'),
                    'is_pep': sanitized_data.get('is_pep', False),
                    'pep_details': sanitized_data.get('pep_details'),
                    'is_public_figure': sanitized_data.get('is_public_figure', False),
                    'public_figure_details': sanitized_data.get('public_figure_details'),
                }
                
                kyc_verification = KYCVerification.objects.create(**kyc_data)
                
                # Perform initial checks
                risk_score, risk_level = KYCService.perform_initial_checks(kyc_verification)
                
                # Log the creation
                AuditService.log_action(
                    user=user,
                    action='KYC verification submitted',
                    entity_type='kyc_verification',
                    entity_id=kyc_verification.kyc_id,
                    new_value={
                        'status': kyc_verification.verification_status,
                        'risk_level': risk_level,
                        'risk_score': risk_score,
                        'first_name': kyc_verification.first_name,
                        'last_name': kyc_verification.last_name
                    }
                )
                
                return {
                    'success': True,
                    'kyc_id': kyc_verification.kyc_id,
                    'status': kyc_verification.verification_status,
                    'risk_level': risk_level,
                    'risk_score': risk_score,
                    'requires_documents': True,
                    'requires_manual_review': risk_level in ['high', 'medium'],
                    'message': 'KYC verification submitted successfully',
                    'created_at': kyc_verification.created_at.isoformat()
                }
        
        except Exception as e:
            return BaseService.handle_exception('create_verification', e, user)
    
    @staticmethod
    def perform_initial_checks(kyc_verification: KYCVerification) -> Tuple[int, str]:
        """Perform initial KYC checks with enhanced risk assessment"""
        try:
            risk_score = 0
            risk_factors = []
            
            # Age check
            try:
                age = kyc_verification.age()
                if age:
                    if age < 18:
                        risk_score = 100  # Automatic rejection
                        risk_factors.append('underage')
                        kyc_verification.verification_status = 'rejected'
                        kyc_verification.rejection_reason = 'Underage'
                    elif age < 21:
                        risk_score += 25
                        risk_factors.append('young_adult')
                    elif age < 25:
                        risk_score += 15
                        risk_factors.append('young_adult')
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not calculate age for KYC {kyc_verification.kyc_id}: {e}")
            
            # Country risk check
            high_risk_countries = getattr(settings, 'HIGH_RISK_COUNTRIES', ['AF', 'IR', 'KP', 'SY', 'YE'])
            medium_risk_countries = getattr(settings, 'MEDIUM_RISK_COUNTRIES', ['RU', 'CN', 'PK', 'NG'])
            
            country = kyc_verification.country_of_residence
            if country:
                country = country.upper()
                if country in high_risk_countries:
                    risk_score += 50
                    risk_factors.append('high_risk_country')
                elif country in medium_risk_countries:
                    risk_score += 25
                    risk_factors.append('medium_risk_country')
            
            # PEP and Public Figure check
            if kyc_verification.is_pep:
                risk_score += 60
                risk_factors.append('pep')
                kyc_verification.pep_status = True
            
            if kyc_verification.is_public_figure:
                risk_score += 40
                risk_factors.append('public_figure')
            
            # Occupation risk
            high_risk_occupations = ['gambling', 'casino', 'adult', 'weapons']
            occupation = (kyc_verification.occupation or '').lower()
            if any(keyword in occupation for keyword in high_risk_occupations):
                risk_score += 30
                risk_factors.append('high_risk_occupation')
            
            # Sanctions list check (simplified)
            sanctions_names = getattr(settings, 'SANCTIONS_LIST', [])
            try:
                full_name = kyc_verification.full_name().lower()
                if any(name.lower() in full_name for name in sanctions_names):
                    risk_score += 100
                    risk_factors.append('sanctions_match')
                    kyc_verification.verification_status = 'rejected'
                    kyc_verification.rejection_reason = 'Sanctions list match'
            except Exception as e:
                logger.warning(f"Could not check sanctions list: {e}")
            
            # Update risk assessment
            if risk_score >= 70:
                risk_level = 'high'
                kyc_verification.requires_enhanced_due_diligence = True
            elif risk_score >= 40:
                risk_level = 'medium'
            else:
                risk_level = 'low'
            
            kyc_verification.risk_score = risk_score
            kyc_verification.risk_level = risk_level
            kyc_verification.risk_factors = risk_factors
            
            # Set initial status
            if kyc_verification.verification_status != 'rejected':
                if risk_level == 'high':
                    kyc_verification.verification_status = 'pending_review'
                else:
                    kyc_verification.verification_status = 'pending_documents'
            
            kyc_verification.save()
            
            return risk_score, risk_level
        
        except Exception as e:
            logger.error(f"Error performing KYC checks: {str(e)}", exc_info=True)
            return {
        'risk_score': 0,
        'risk_level': 'low',
        'requires_tac': False,
        'requires_video_call': False,
        'requires_manual_review': False,
        'priority': 'normal'
    }
    
    @staticmethod
    def upload_document(kyc_verification: KYCVerification, user: 'User', document_data: Dict[str, Any], file) -> Dict[str, Any]:
        """Upload a document for KYC verification"""
        try:
            # Validate document data
            required_fields = ['document_type', 'document_name']
            valid, error_msg = BaseService.validate_required_fields(document_data, required_fields)
            if not valid:
                return {'success': False, 'error': error_msg}
            
            if not file:
                return {'success': False, 'error': 'File is required'}
            
            # Validate file
            validation_result = DocumentService.validate_document(file)
            if not validation_result.get('valid', False):
                return {'success': False, 'error': validation_result.get('error', 'Invalid document')}
            
            # Save file
            file_path, file_hash, file_size = DocumentService.save_document(
                file, user.id, document_data['document_type']
            )
            
            # Check for duplicate documents of the same type
            existing_doc = KYCDocument.objects.filter(
                kyc_verification=kyc_verification,
                document_type=document_data['document_type'],
                status='approved'
            ).exists()
            
            if existing_doc:
                return {
                    'success': False,
                    'error': f'Document of type {document_data["document_type"]} already approved'
                }
            
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
                issuing_authority=document_data.get('issuing_authority'),
                is_primary=document_data.get('is_primary', False)
            )
            
            # Update KYC status
            kyc_verification.documents_submitted += 1
            
            # Check if enough documents submitted
            min_documents = getattr(settings, 'MIN_KYC_DOCUMENTS', 2)
            if kyc_verification.documents_submitted >= min_documents:
                if kyc_verification.verification_status == 'pending_documents':
                    kyc_verification.verification_status = 'pending_review'
            
            kyc_verification.save()
            
            # Log the upload
            AuditService.log_action(
                user=user,
                action='KYC document uploaded',
                entity_type='kyc_document',
                entity_id=document.document_id,
                new_value={
                    'type': document.document_type,
                    'file_name': document.original_file_name,
                    'file_size': document.file_size,
                    'kyc_id': kyc_verification.kyc_id
                }
            )
            
            return {
                'success': True,
                'document_id': document.document_id,
                'file_name': document.original_file_name,
                'status': document.status,
                'document_type': document.document_type,
                'kyc_id': kyc_verification.kyc_id,
                'uploaded_at': document.created_at.isoformat(),
                'message': 'Document uploaded successfully'
            }
        
        except Exception as e:
            return BaseService.handle_exception('upload_document', e, user)
    
    @staticmethod
    def verify_document(document: KYCDocument, verified_by: 'User', status: str, notes: str = '', rejection_reason: str = '') -> Dict[str, Any]:
        """Verify a KYC document"""
        try:
            if status not in ['approved', 'rejected']:
                return {'success': False, 'error': 'Invalid status. Must be "approved" or "rejected"'}
            
            with transaction.atomic():
                # Update document
                old_status = document.status
                document.status = status
                document.verified_by = verified_by
                document.verified_at = timezone.now()
                document.notes = notes
                document.rejection_reason = rejection_reason if status == 'rejected' else ''
                document.save()
                
                # Update KYC verification
                kyc = document.kyc_verification
                if status == 'approved':
                    kyc.documents_approved += 1
                    # Mark as primary if it's the first approved ID document
                    if document.document_type in ['passport', 'national_id', 'drivers_license']:
                        KYCDocument.objects.filter(
                            kyc_verification=kyc,
                            document_type=document.document_type
                        ).exclude(pk=document.pk).update(is_primary=False)
                        document.is_primary = True
                        document.save()
                elif status == 'rejected':
                    kyc.documents_rejected += 1
                
                # Check verification completion
                min_approved = getattr(settings, 'MIN_APPROVED_DOCUMENTS', 1)
                if kyc.documents_approved >= min_approved:
                    kyc.document_verification_completed = True
                    if kyc.risk_level != 'high':
                        kyc.verification_status = 'pending_final_review'
                
                kyc.save()
                
                # Log the verification
                AuditService.log_action(
                    user=verified_by,
                    action=f'Document {status}: {document.document_id}',
                    entity_type='kyc_document',
                    entity_id=document.document_id,
                    old_value={'status': old_status},
                    new_value={
                        'status': status,
                        'verified_by': verified_by.email,
                        'verified_at': timezone.now().isoformat(),
                        'notes': notes,
                        'rejection_reason': rejection_reason,
                        'kyc_id': kyc.kyc_id
                    }
                )
                
                return {
                    'success': True,
                    'document_id': document.document_id,
                    'status': status,
                    'verified_at': document.verified_at.isoformat(),
                    'document_type': document.document_type,
                    'kyc_id': kyc.kyc_id,
                    'message': f'Document {status} successfully'
                }
        
        except Exception as e:
            return BaseService.handle_exception('verify_document', e, verified_by)
    
    @staticmethod
    def approve_verification(kyc_verification: KYCVerification, approved_by: 'User', notes: str = '', compliance_level: str = 'standard') -> Dict[str, Any]:
        """Approve KYC verification"""
        try:
            with transaction.atomic():
                # Validate verification can be approved
                valid_statuses = ['pending_final_review', 'pending_review', 'under_review']
                if kyc_verification.verification_status not in valid_statuses:
                    return {
                        'success': False,
                        'error': f'KYC cannot be approved in current status: {kyc_verification.verification_status}'
                    }
                
                if not kyc_verification.document_verification_completed:
                    return {
                        'success': False,
                        'error': 'Document verification not completed'
                    }
                
                # Update verification
                old_status = kyc_verification.verification_status
                kyc_verification.verification_status = 'approved'
                kyc_verification.compliance_level = compliance_level
                kyc_verification.verified_by = approved_by
                kyc_verification.verified_at = timezone.now()
                kyc_verification.review_notes = notes
                
                # Calculate next review date (1 year from now by default)
                if not kyc_verification.next_review_date:
                    kyc_verification.next_review_date = timezone.now() + timedelta(days=365)
                
                kyc_verification.save()
                
                # Update user compliance profile
                profile, created = ComplianceProfile.objects.get_or_create(user=kyc_verification.user)
                profile.kyc_verified = True
                profile.kyc_verification_date = timezone.now()
                profile.kyc_expiry_date = kyc_verification.next_review_date
                profile.compliance_level = compliance_level
                profile.compliance_status = 'verified'
                profile.risk_level = kyc_verification.risk_level
                profile.save()
                
                # Log the approval
                AuditService.log_action(
                    user=approved_by,
                    action=f'KYC approved: {kyc_verification.kyc_id}',
                    entity_type='kyc_verification',
                    entity_id=kyc_verification.kyc_id,
                    old_value={'status': old_status},
                    new_value={
                        'status': 'approved',
                        'compliance_level': compliance_level,
                        'verified_by': approved_by.email,
                        'verified_at': timezone.now().isoformat(),
                        'next_review_date': kyc_verification.next_review_date.isoformat(),
                        'notes': notes
                    }
                )
                
                # Send approval email
                full_name = kyc_verification.full_name()
                send_kyc_approved_email(
                    kyc_verification.email,
                    full_name,
                    compliance_level,
                    kyc_verification.kyc_id,
                    kyc_verification.next_review_date
                )
                
                # Create alert for successful verification
                AlertService.create_alert(
                    alert_type='kyc_approved',
                    severity='success',
                    title=f"KYC Approved: {kyc_verification.kyc_id}",
                    description=f"KYC verification for {full_name} has been approved",
                    kyc_verification=kyc_verification,
                    user=approved_by
                )
                
                return {
                    'success': True,
                    'kyc_id': kyc_verification.kyc_id,
                    'status': 'approved',
                    'compliance_level': compliance_level,
                    'verified_at': kyc_verification.verified_at.isoformat(),
                    'next_review_date': kyc_verification.next_review_date.isoformat(),
                    'verified_by': approved_by.email,
                    'message': 'KYC verification approved'
                }
        
        except Exception as e:
            return BaseService.handle_exception('approve_verification', e, approved_by)
    
    @staticmethod
    def reject_verification(kyc_verification: KYCVerification, rejected_by: 'User', reason: str) -> Dict[str, Any]:
        """Reject KYC verification"""
        try:
            with transaction.atomic():
                # Update verification
                old_status = kyc_verification.verification_status
                kyc_verification.verification_status = 'rejected'
                kyc_verification.verified_by = rejected_by
                kyc_verification.verified_at = timezone.now()
                kyc_verification.rejection_reason = reason
                kyc_verification.save()
                
                # Update user compliance profile
                profile = getattr(kyc_verification.user, 'compliance_profile', None)
                if profile:
                    profile.kyc_verified = False
                    profile.compliance_status = 'rejected'
                    profile.risk_level = max(profile.risk_level, kyc_verification.risk_level)
                    profile.save()
                
                # Log the rejection
                AuditService.log_action(
                    user=rejected_by,
                    action=f'KYC rejected: {kyc_verification.kyc_id}',
                    entity_type='kyc_verification',
                    entity_id=kyc_verification.kyc_id,
                    old_value={'status': old_status},
                    new_value={
                        'status': 'rejected',
                        'rejection_reason': reason,
                        'verified_by': rejected_by.email,
                        'verified_at': timezone.now().isoformat()
                    }
                )
                
                # Send rejection email
                full_name = kyc_verification.full_name()
                send_kyc_rejected_email(
                    kyc_verification.email,
                    full_name,
                    reason,
                    kyc_verification.kyc_id
                )
                
                # Create alert for rejected KYC
                AlertService.create_alert(
                    alert_type='kyc_rejected',
                    severity='warning',
                    title=f"KYC Rejected: {kyc_verification.kyc_id}",
                    description=f"KYC verification for {full_name} has been rejected. Reason: {reason}",
                    kyc_verification=kyc_verification,
                    user=rejected_by
                )
                
                return {
                    'success': True,
                    'kyc_id': kyc_verification.kyc_id,
                    'status': 'rejected',
                    'rejection_reason': reason,
                    'verified_at': kyc_verification.verified_at.isoformat(),
                    'verified_by': rejected_by.email,
                    'message': 'KYC verification rejected'
                }
        
        except Exception as e:
            return BaseService.handle_exception('reject_verification', e, rejected_by)
    
    @staticmethod
    def request_document_revision(document: KYCDocument, requested_by: 'User', revision_notes: str) -> Dict[str, Any]:
        """Request revision of a KYC document"""
        try:
            # Update document
            old_status = document.status
            document.status = 'revision_required'
            document.revision_notes = revision_notes
            document.revision_requested_by = requested_by
            document.revision_requested_at = timezone.now()
            document.save()
            
            # Log the revision request
            AuditService.log_action(
                user=requested_by,
                action=f'Document revision requested: {document.document_id}',
                entity_type='kyc_document',
                entity_id=document.document_id,
                old_value={'status': old_status},
                new_value={
                    'status': 'revision_required',
                    'revision_notes': revision_notes,
                    'requested_by': requested_by.email,
                    'requested_at': timezone.now().isoformat(),
                    'kyc_id': document.kyc_verification.kyc_id
                }
            )
            
            # Create alert for user
            AlertService.create_alert(
                alert_type='document_revision',
                severity='info',
                title=f"Document revision required: {document.document_id}",
                description=revision_notes,
                kyc_verification=document.kyc_verification,
                user=document.user
            )
            
            return {
                'success': True,
                'document_id': document.document_id,
                'status': 'revision_required',
                'revision_notes': revision_notes,
                'requested_by': requested_by.email,
                'kyc_id': document.kyc_verification.kyc_id,
                'message': 'Document revision requested'
            }
        
        except Exception as e:
            return BaseService.handle_exception('request_document_revision', e, requested_by)


class TACService(BaseService):
    """Service for TAC operations"""
    
    @staticmethod
    def generate_tac(user: 'User', **kwargs) -> Dict[str, Any]:
        """Generate a new TAC"""
        try:
            # Validate user
            if not user or not isinstance(user, User):
                return {'success': False, 'error': 'Valid user required'}
            
            if not user.email:
                return {'success': False, 'error': 'User email is required'}
            
            # Check rate limiting
            recent_tacs = TACRequest.objects.filter(
                user=user,
                created_at__gte=timezone.now() - timedelta(minutes=5)
            ).count()
            
            if recent_tacs >= 3:
                return {
                    'success': False,
                    'error': 'Too many TAC requests. Please try again later.'
                }
            
            # Generate TAC code
            tac_code = TACService._generate_tac_code()
            
            # Calculate expiry
            expiry_minutes = kwargs.get('expiry_minutes', 5)
            expires_at = timezone.now() + timedelta(minutes=expiry_minutes)
            
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
                device_id=kwargs.get('device_id'),
                compliance_request=kwargs.get('compliance_request')
            )
            
            # Send TAC via email
            user_name = user.get_full_name() or user.username
            send_tac_email(
                user.email,
                tac_code,
                user_name,
                tac_request.purpose,
                tac_request.expires_at
            )
            
            # Log the generation
            AuditService.log_action(
                user=user,
                action='TAC generated',
                entity_type='tac_request',
                entity_id=tac_request.tac_id,
                new_value={
                    'tac_type': tac_request.tac_type,
                    'purpose': tac_request.purpose,
                    'sent_to': tac_request.sent_to,
                    'expires_at': expires_at.isoformat()
                }
            )
            
            return {
                'success': True,
                'tac_id': tac_request.tac_id,
                'sent_to': user.email,
                'sent_via': 'email',
                'expires_at': expires_at.isoformat(),
                'time_remaining': expiry_minutes * 60,
                'message': 'TAC sent successfully'
            }
        
        except Exception as e:
            return BaseService.handle_exception('generate_tac', e, user)
    
    @staticmethod
    def verify_tac(user: 'User', tac_code: str, **kwargs) -> Dict[str, Any]:
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
                        # Block further attempts for some time
                        AlertService.create_alert(
                            alert_type='tac_brute_force',
                            severity='warning',
                            title=f"Multiple failed TAC attempts: {user.email}",
                            description=f"User exceeded maximum TAC attempts",
                            user=user
                        )
                    expired_tac.save()
                
                return {
                    'success': False,
                    'error': 'Invalid or expired TAC code'
                }
            
            # Additional verification checks
            if not TACService._validate_tac_context(tac_request, kwargs):
                return {
                    'success': False,
                    'error': 'TAC context mismatch'
                }
            
            # Mark TAC as used
            tac_request.is_used = True
            tac_request.used_at = timezone.now()
            tac_request.used_ip = kwargs.get('ip_address')
            tac_request.used_device_id = kwargs.get('device_id')
            tac_request.save()
            
            # Log the verification
            AuditService.log_action(
                user=user,
                action='TAC verified',
                entity_type='tac_request',
                entity_id=tac_request.tac_id,
                new_value={
                    'is_used': True,
                    'used_at': timezone.now().isoformat(),
                    'used_ip': tac_request.used_ip
                }
            )
            
            # If TAC is for compliance request, update it
            if tac_request.compliance_request:
                compliance_request = tac_request.compliance_request
                compliance_request.tac_verified_at = timezone.now()
                compliance_request.tac_verified_ip = tac_request.used_ip
                compliance_request.save()
            
            return {
                'success': True,
                'tac_id': tac_request.tac_id,
                'verified_at': tac_request.used_at.isoformat(),
                'purpose': tac_request.purpose,
                'compliance_request_id': tac_request.compliance_request.compliance_id if tac_request.compliance_request else None,
                'message': 'TAC verified successfully'
            }
        
        except Exception as e:
            return BaseService.handle_exception('verify_tac', e, user)
    
    @staticmethod
    def _validate_tac_context(tac_request: TACRequest, verification_context: Dict[str, Any]) -> bool:
        """Validate TAC context matches original request"""
        # Check amount if provided
        if verification_context.get('amount') and tac_request.amount:
            if float(verification_context['amount']) != float(tac_request.amount):
                return False
        
        # Check transaction ID if provided
        if verification_context.get('transaction_id') and tac_request.transaction_id:
            if verification_context['transaction_id'] != tac_request.transaction_id:
                return False
        
        # Check device ID if provided
        if verification_context.get('device_id') and tac_request.device_id:
            if verification_context['device_id'] != tac_request.device_id:
                return False
        
        return True
    
    @staticmethod
    def resend_tac(tac_request: TACRequest) -> Dict[str, Any]:
        """Resend a TAC"""
        try:
            # Check if TAC is still valid
            if tac_request.is_expired or tac_request.is_used:
                return {
                    'success': False,
                    'error': 'TAC is no longer valid'
                }
            
            if tac_request.expires_at <= timezone.now():
                return {
                    'success': False,
                    'error': 'TAC has expired'
                }
            
            # Check resend limit
            if tac_request.delivery_attempts >= 3:
                return {
                    'success': False,
                    'error': 'Maximum resend attempts reached'
                }
            
            # Resend TAC
            user_name = tac_request.user.get_full_name() or tac_request.user.username
            send_tac_email(
                tac_request.sent_to,
                tac_request.tac_code,
                user_name,
                tac_request.purpose,
                tac_request.expires_at
            )
            
            tac_request.delivery_attempts += 1
            tac_request.last_resend_at = timezone.now()
            tac_request.save()
            
            # Log the resend
            AuditService.log_action(
                user=tac_request.user,
                action='TAC resent',
                entity_type='tac_request',
                entity_id=tac_request.tac_id,
                new_value={
                    'delivery_attempts': tac_request.delivery_attempts,
                    'last_resend_at': timezone.now().isoformat()
                }
            )
            
            return {
                'success': True,
                'tac_id': tac_request.tac_id,
                'sent_to': tac_request.sent_to,
                'expires_at': tac_request.expires_at.isoformat(),
                'delivery_attempts': tac_request.delivery_attempts,
                'message': 'TAC resent successfully'
            }
        
        except Exception as e:
            return BaseService.handle_exception('resend_tac', e, tac_request.user)
    
    @staticmethod
    def _generate_tac_code(length: int = 6) -> str:
        """Generate a secure TAC code"""
        return ''.join([str(secrets.randbelow(10)) for _ in range(length)])
    
    @staticmethod
    def generate_and_store_recovery_code(user: 'User', purpose: str = 'account_recovery') -> Dict[str, Any]:
        """Generate a recovery code for account recovery"""
        try:
            recovery_code = secrets.token_hex(16)  # 32 character hex code
            
            # Store recovery code
            tac_request = TACRequest.objects.create(
                user=user,
                tac_code=recovery_code,
                tac_type='recovery',
                purpose=purpose,
                sent_via='system',
                sent_to=user.email,
                expires_at=timezone.now() + timedelta(hours=24),
                is_used=False
            )
            
            # Log generation
            AuditService.log_action(
                user=user,
                action='Recovery code generated',
                entity_type='tac_request',
                entity_id=tac_request.tac_id,
                new_value={
                    'purpose': purpose, 
                    'expires_at': tac_request.expires_at.isoformat(),
                    'code_type': 'recovery'
                }
            )
            
            return {
                'success': True,
                'recovery_code_id': tac_request.tac_id,
                'expires_at': tac_request.expires_at.isoformat(),
                'message': 'Recovery code generated'
            }
        
        except Exception as e:
            return BaseService.handle_exception('generate_recovery_code', e, user)


class VideoCallService(BaseService):
    """Service for video call operations"""
    
    @staticmethod
    def schedule_call(requested_by: 'User', **kwargs) -> Dict[str, Any]:
        """Schedule a video call"""
        try:
            # Get compliance request
            compliance_request = kwargs.get('compliance_request')
            if not compliance_request:
                return {
                    'success': False,
                    'error': 'Compliance request is required'
                }
            
            # Validate scheduled time
            scheduled_for = kwargs.get('scheduled_for')
            if not scheduled_for:
                return {
                    'success': False,
                    'error': 'Scheduled time is required'
                }
            
            # Ensure scheduled_for is timezone aware
            if timezone.is_naive(scheduled_for):
                scheduled_for = timezone.make_aware(scheduled_for)
            
            if scheduled_for <= timezone.now() + timedelta(minutes=15):
                return {
                    'success': False,
                    'error': 'Scheduled time must be at least 15 minutes from now'
                }
            
            # Create video call session
            video_call = VideoCallSession.objects.create(
                user=compliance_request.user,
                compliance_request=compliance_request,
                purpose=kwargs.get('purpose', 'KYC Verification'),
                scheduled_for=scheduled_for,
                duration_minutes=kwargs.get('duration_minutes', 30),
                agent=kwargs.get('agent'),
                platform=kwargs.get('platform', 'zoom'),
                meeting_link=kwargs.get('meeting_link'),
                meeting_id=kwargs.get('meeting_id'),
                meeting_password=kwargs.get('meeting_password'),
                timezone=kwargs.get('timezone', 'UTC'),
                agenda=kwargs.get('agenda'),
                required_documents=kwargs.get('required_documents'),
                additional_instructions=kwargs.get('additional_instructions')
            )
            
            # Update compliance request
            compliance_request.video_call_scheduled_at = video_call.scheduled_for
            compliance_request.video_call_link = video_call.meeting_link
            compliance_request.video_call_status = 'scheduled'
            compliance_request.save()
            
            # Send notification emails
            user_name = compliance_request.user.get_full_name() or compliance_request.user.email
            send_video_call_scheduled_email(
                compliance_request.user_email,
                user_name,
                video_call.scheduled_for,
                video_call.meeting_link,
                video_call.meeting_password,
                video_call.platform,
                video_call.duration_minutes,
                video_call.agenda,
                video_call.required_documents
            )
            
            # Log the scheduling
            AuditService.log_action(
                user=requested_by,
                action='Video call scheduled',
                entity_type='video_call',
                entity_id=video_call.session_id,
                new_value={
                    'scheduled_for': video_call.scheduled_for.isoformat(),
                    'platform': video_call.platform,
                    'purpose': video_call.purpose,
                    'compliance_request_id': compliance_request.compliance_id
                }
            )
            
            return {
                'success': True,
                'session_id': video_call.session_id,
                'scheduled_for': video_call.scheduled_for.isoformat(),
                'meeting_link': video_call.meeting_link,
                'platform': video_call.platform,
                'duration_minutes': video_call.duration_minutes,
                'compliance_request_id': compliance_request.compliance_id,
                'message': 'Video call scheduled successfully'
            }
        
        except Exception as e:
            return BaseService.handle_exception('schedule_call', e, requested_by)
    
    @staticmethod
    def start_call(video_call: VideoCallSession) -> Dict[str, Any]:
        """Start a video call"""
        try:
            # Check if call can be started
            if video_call.status != 'scheduled':
                return {
                    'success': False,
                    'error': f'Cannot start call in current status: {video_call.status}'
                }
            
            # Check if scheduled time has arrived
            if video_call.scheduled_for > timezone.now() + timedelta(minutes=5):
                return {
                    'success': False,
                    'error': 'Call cannot start more than 5 minutes before scheduled time'
                }
            
            # Update call status
            video_call.status = 'in_progress'
            video_call.started_at = timezone.now()
            video_call.actual_start_time = timezone.now()
            video_call.save()
            
            # Update compliance request
            video_call.compliance_request.video_call_status = 'in_progress'
            video_call.compliance_request.save()
            
            # Log the start
            AuditService.log_action(
                user=video_call.user,
                action='Video call started',
                entity_type='video_call',
                entity_id=video_call.session_id,
                new_value={
                    'status': 'in_progress',
                    'started_at': timezone.now().isoformat(),
                    'compliance_request_id': video_call.compliance_request.compliance_id
                }
            )
            
            return {
                'success': True,
                'session_id': video_call.session_id,
                'status': video_call.status,
                'started_at': video_call.started_at.isoformat(),
                'compliance_request_id': video_call.compliance_request.compliance_id,
                'message': 'Video call started'
            }
        
        except Exception as e:
            return BaseService.handle_exception('start_call', e, video_call.user)
    
    @staticmethod
    def complete_call(video_call: VideoCallSession, completed_by: 'User', verification_passed: bool = False, notes: str = '') -> Dict[str, Any]:
        """Complete a video call"""
        try:
            # Update call status
            video_call.status = 'completed'
            video_call.ended_at = timezone.now()
            video_call.verification_passed = verification_passed
            video_call.verification_notes = notes
            video_call.completed_by = completed_by
            
            # Calculate duration
            if video_call.started_at:
                duration = (video_call.ended_at - video_call.started_at).total_seconds() / 60
                video_call.actual_duration = int(duration)
            
            video_call.save()
            
            # Update compliance request
            compliance_request = video_call.compliance_request
            compliance_request.video_call_completed_at = timezone.now()
            compliance_request.video_call_notes = notes
            compliance_request.video_call_status = 'completed'
            
            if verification_passed:
                compliance_request.status = 'under_review'
                compliance_request.video_call_verification_passed = True
            else:
                compliance_request.status = 'info_required'
                compliance_request.review_notes = f"Video call verification failed: {notes}"
                compliance_request.video_call_verification_passed = False
            
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
                    'notes': notes,
                    'actual_duration': video_call.actual_duration,
                    'compliance_request_id': compliance_request.compliance_id
                }
            )
            
            # Create alert based on outcome
            alert_severity = 'success' if verification_passed else 'warning'
            alert_description = f"Video call {'passed' if verification_passed else 'failed'}: {notes}"
            
            AlertService.create_alert(
                alert_type='video_call_completed',
                severity=alert_severity,
                title=f"Video call completed: {video_call.session_id}",
                description=alert_description,
                compliance_request=compliance_request,
                user=completed_by
            )
            
            return {
                'success': True,
                'session_id': video_call.session_id,
                'status': video_call.status,
                'verification_passed': verification_passed,
                'actual_duration': video_call.actual_duration,
                'compliance_request_id': compliance_request.compliance_id,
                'completed_by': completed_by.email,
                'message': 'Video call completed'
            }
        
        except Exception as e:
            return BaseService.handle_exception('complete_call', e, completed_by)
    
    @staticmethod
    def reschedule_call(video_call: VideoCallSession, new_time: datetime, rescheduled_by: 'User', reason: str = '') -> Dict[str, Any]:
        """Reschedule a video call"""
        try:
            # Check if call can be rescheduled
            if video_call.status not in ['scheduled', 'rescheduled']:
                return {
                    'success': False,
                    'error': f'Cannot reschedule call in current status: {video_call.status}'
                }
            
            # Ensure new_time is timezone aware
            if timezone.is_naive(new_time):
                new_time = timezone.make_aware(new_time)
            
            if new_time <= timezone.now() + timedelta(minutes=15):
                return {
                    'success': False,
                    'error': 'Rescheduled time must be at least 15 minutes from now'
                }
            
            # Update call
            old_time = video_call.scheduled_for
            video_call.status = 'rescheduled'
            video_call.scheduled_for = new_time
            video_call.rescheduled_by = rescheduled_by
            video_call.rescheduled_at = timezone.now()
            video_call.reschedule_reason = reason
            video_call.reschedule_count = video_call.reschedule_count + 1
            video_call.save()
            
            # Update compliance request
            video_call.compliance_request.video_call_scheduled_at = new_time
            video_call.compliance_request.save()
            
            # Send reschedule notification
            user_name = video_call.user.get_full_name() or video_call.user.email
            send_video_call_scheduled_email(
                video_call.user.email,
                user_name,
                new_time,
                video_call.meeting_link,
                video_call.meeting_password,
                video_call.platform,
                video_call.duration_minutes,
                video_call.agenda,
                video_call.required_documents,
                is_reschedule=True,
                reason=reason
            )
            
            # Log the rescheduling
            AuditService.log_action(
                user=rescheduled_by,
                action='Video call rescheduled',
                entity_type='video_call',
                entity_id=video_call.session_id,
                old_value={'scheduled_for': old_time.isoformat()},
                new_value={
                    'scheduled_for': new_time.isoformat(),
                    'status': 'rescheduled',
                    'reschedule_reason': reason,
                    'rescheduled_by': rescheduled_by.email
                }
            )
            
            return {
                'success': True,
                'session_id': video_call.session_id,
                'scheduled_for': new_time.isoformat(),
                'reschedule_count': video_call.reschedule_count,
                'rescheduled_by': rescheduled_by.email,
                'message': 'Video call rescheduled'
            }
        
        except Exception as e:
            return BaseService.handle_exception('reschedule_call', e, rescheduled_by)
    
    @staticmethod
    def cancel_call(video_call: VideoCallSession, cancelled_by: 'User', reason: str = '') -> Dict[str, Any]:
        """Cancel a video call"""
        try:
            # Update call
            old_status = video_call.status
            video_call.status = 'cancelled'
            video_call.cancelled_by = cancelled_by
            video_call.cancelled_at = timezone.now()
            video_call.cancellation_reason = reason
            video_call.save()
            
            # Update compliance request
            compliance_request = video_call.compliance_request
            compliance_request.review_notes = f"Video call cancelled: {reason}"
            compliance_request.video_call_status = 'cancelled'
            compliance_request.save()
            
            # Log the cancellation
            AuditService.log_action(
                user=cancelled_by,
                action='Video call cancelled',
                entity_type='video_call',
                entity_id=video_call.session_id,
                old_value={'status': old_status},
                new_value={
                    'status': 'cancelled',
                    'reason': reason,
                    'cancelled_by': cancelled_by.email,
                    'cancelled_at': timezone.now().isoformat()
                }
            )
            
            # Create alert
            AlertService.create_alert(
                alert_type='video_call_cancelled',
                severity='warning',
                title=f"Video call cancelled: {video_call.session_id}",
                description=f"Video call cancelled by {cancelled_by.email}. Reason: {reason}",
                compliance_request=compliance_request,
                user=cancelled_by
            )
            
            return {
                'success': True,
                'session_id': video_call.session_id,
                'status': video_call.status,
                'cancellation_reason': reason,
                'cancelled_by': cancelled_by.email,
                'compliance_request_id': compliance_request.compliance_id,
                'message': 'Video call cancelled'
            }
        
        except Exception as e:
            return BaseService.handle_exception('cancel_call', e, cancelled_by)
    
    @staticmethod
    def join_call(video_call: VideoCallSession, user: 'User', join_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Record user joining a video call"""
        try:
            if not join_time:
                join_time = timezone.now()
            
            # Record join time
            if user == video_call.user:
                video_call.user_joined_at = join_time
            elif user == video_call.agent:
                video_call.agent_joined_at = join_time
            else:
                return {
                    'success': False,
                    'error': 'User not authorized to join this call'
                }
            
            video_call.save()
            
            # Log the join
            user_type = 'user' if user == video_call.user else 'agent'
            AuditService.log_action(
                user=user,
                action='Joined video call',
                entity_type='video_call',
                entity_id=video_call.session_id,
                new_value={
                    'joined_at': join_time.isoformat(),
                    'user_type': user_type,
                    'compliance_request_id': video_call.compliance_request.compliance_id
                }
            )
            
            return {
                'success': True,
                'session_id': video_call.session_id,
                'joined_at': join_time.isoformat(),
                'user_type': user_type,
                'message': 'Joined video call'
            }
        
        except Exception as e:
            return BaseService.handle_exception('join_call', e, user)
    
    @staticmethod
    def add_call_notes(video_call: VideoCallSession, user: 'User', notes: str, note_type: str = 'general') -> Dict[str, Any]:
        """Add notes to a video call"""
        try:
            # Create notes entry
            current_notes = video_call.additional_notes or {}
            if 'call_notes' not in current_notes:
                current_notes['call_notes'] = []
            
            current_notes['call_notes'].append({
                'timestamp': timezone.now().isoformat(),
                'user': user.email,
                'user_id': user.id,
                'note_type': note_type,
                'notes': notes
            })
            
            video_call.additional_notes = current_notes
            video_call.save()
            
            # Log the note addition
            AuditService.log_action(
                user=user,
                action='Added call notes',
                entity_type='video_call',
                entity_id=video_call.session_id,
                new_value={
                    'note_type': note_type,
                    'has_notes': True,
                    'compliance_request_id': video_call.compliance_request.compliance_id
                }
            )
            
            return {
                'success': True,
                'session_id': video_call.session_id,
                'note_count': len(current_notes['call_notes']),
                'added_by': user.email,
                'message': 'Call notes added'
            }
        
        except Exception as e:
            return BaseService.handle_exception('add_call_notes', e, user)


class DocumentService(BaseService):
    """Service for document operations"""
    
    @staticmethod
    def save_document(file, user_id: int, doc_type: str) -> Tuple[str, str, int]:
        """Save uploaded document and return metadata"""
        try:
            # Create secure directory structure
            timestamp = int(timezone.now().timestamp())
            safe_user_id = str(user_id).replace('/', '_').replace('\\', '_')
            safe_doc_type = str(doc_type).replace('/', '_').replace('\\', '_')
            
            # Create directory
            user_dir = f"compliance/documents/{safe_user_id}/{timestamp}"
            full_dir = os.path.join(settings.MEDIA_ROOT, user_dir)
            os.makedirs(full_dir, exist_ok=True)
            
            # Generate secure filename
            file_extension = os.path.splitext(file.name)[1].lower()
            if not file_extension:
                content_type = file.content_type
                file_extension = mimetypes.guess_extension(content_type) or '.bin'
            
            # Validate file extension
            allowed_extensions = getattr(settings, 'ALLOWED_DOCUMENT_EXTENSIONS', 
                                       ['.jpg', '.jpeg', '.png', '.pdf', '.doc', '.docx'])
            if file_extension.lower() not in allowed_extensions:
                raise ValidationError(f"File extension {file_extension} not allowed")
            
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
            file_size = os.path.getsize(full_path) if os.path.exists(full_path) else file.size
            
            logger.info(f"Document saved: {saved_path}, size: {file_size} bytes, hash: {file_hash[:16] if file_hash else 'N/A'}")
            
            return saved_path, file_hash, file_size
        
        except Exception as e:
            logger.error(f"Error saving document: {e}", exc_info=True)
            raise
    
    @staticmethod
    def _hash_file(file_path: str) -> Optional[str]:
        """Generate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error hashing file {file_path}: {e}", exc_info=True)
            return None
    
    @staticmethod
    def validate_document(file) -> Dict[str, Any]:
        """Validate document before saving"""
        try:
            # Check file size
            max_size = 10 * 1024 * 1024  # 10MB
            if file.size > max_size:
                return {
                    'valid': False,
                    'error': f'File size exceeds {max_size/1024/1024}MB limit'
                }
            
            # Check file type
            allowed_types = getattr(settings, 'ALLOWED_DOCUMENT_TYPES', 
                                  ['image/jpeg', 'image/png', 'application/pdf'])
            
            if file.content_type not in allowed_types:
                return {
                    'valid': False,
                    'error': f'File type {file.content_type} not allowed'
                }
            
            # Check for malicious content (basic check)
            dangerous_extensions = ['.exe', '.bat', '.cmd', '.sh', '.php', '.js', '.vbs']
            file_name_lower = file.name.lower()
            if any(file_name_lower.endswith(ext) for ext in dangerous_extensions):
                return {
                    'valid': False,
                    'error': 'Potentially malicious file type detected'
                }
            
            # Check file name length
            if len(file.name) > 255:
                return {
                    'valid': False,
                    'error': 'File name too long (max 255 characters)'
                }
            
            return {
                'valid': True,
                'file_size': file.size,
                'file_type': file.content_type,
                'file_name': file.name,
                'file_extension': os.path.splitext(file.name)[1].lower()
            }
        
        except Exception as e:
            return BaseService.handle_exception('validate_document', e)
    
    @staticmethod
    def delete_document(document: KYCDocument) -> Dict[str, Any]:
        """Delete a document from storage"""
        try:
            document_id = document.document_id
            file_path = document.file_path
            
            # Delete file from storage
            if file_path and default_storage.exists(file_path):
                default_storage.delete(file_path)
            
            # Delete database record
            document.delete()
            
            # Log deletion
            AuditService.log_action(
                user=document.user,
                action='Document deleted',
                entity_type='kyc_document',
                entity_id=document_id,
                old_value={'file_path': file_path}
            )
            
            return {
                'success': True,
                'document_id': document_id,
                'message': 'Document deleted successfully'
            }
        
        except Exception as e:
            return BaseService.handle_exception('delete_document', e, document.user)
    
    @staticmethod
    def get_document_url(document: KYCDocument) -> Optional[str]:
        """Get secure URL for document access"""
        try:
            if not document.file_path:
                return None
                
            if hasattr(default_storage, 'url'):
                return default_storage.url(document.file_path)
            else:
                # Generate signed URL for cloud storage
                return DocumentService._generate_signed_url(document.file_path)
        except Exception as e:
            logger.error(f"Error generating document URL: {e}", exc_info=True)
            return None
    
    @staticmethod
    def _generate_signed_url(file_path: str) -> str:
        """Generate signed URL for secure document access"""
        # This would integrate with cloud storage signed URL generation
        # For now, return a placeholder
        return f"/media/{file_path}"


class AuditService(BaseService):
    """Service for audit logging"""
    
    @staticmethod
    def log_action(user: Optional['User'], action: str, entity_type: str, entity_id: str, 
                  old_value: Optional[Dict] = None, new_value: Optional[Dict] = None, **kwargs) -> Optional[ComplianceAuditLog]:
        """Log an action to audit trail"""
        try:
            audit_log = ComplianceAuditLog.objects.create(
                user=user,
                user_email=user.email if user and hasattr(user, 'email') else None,
                user_role=kwargs.get('user_role'),
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                old_value=old_value,
                new_value=new_value,
                ip_address=kwargs.get('ip_address'),
                user_agent=kwargs.get('user_agent'),
                location=kwargs.get('location'),
                device_id=kwargs.get('device_id'),
                session_id=kwargs.get('session_id'),
                source=kwargs.get('source', 'backend'),
                metadata=kwargs.get('metadata', {})
            )
            
            logger.info(f"Audit log created: {action} for {entity_type} {entity_id}")
            return audit_log
        
        except Exception as e:
            logger.error(f"Error creating audit log: {e}", exc_info=True)
            return None
    
    @staticmethod
    def search_logs(**filters) -> Dict[str, Any]:
        """Search audit logs with filters"""
        try:
            queryset = ComplianceAuditLog.objects.all()
            
            # Apply filters
            if filters.get('user_id'):
                queryset = queryset.filter(user_id=filters['user_id'])
            
            if filters.get('entity_type'):
                queryset = queryset.filter(entity_type=filters['entity_type'])
            
            if filters.get('entity_id'):
                queryset = queryset.filter(entity_id=filters['entity_id'])
            
            if filters.get('action'):
                queryset = queryset.filter(action__icontains=filters['action'])
            
            if filters.get('start_date'):
                queryset = queryset.filter(created_at__gte=filters['start_date'])
            
            if filters.get('end_date'):
                queryset = queryset.filter(created_at__lte=filters['end_date'])
            
            if filters.get('ip_address'):
                queryset = queryset.filter(ip_address=filters['ip_address'])
            
            if filters.get('user_email'):
                queryset = queryset.filter(user_email__icontains=filters['user_email'])
            
            # Order by creation date
            queryset = queryset.order_by('-created_at')
            
            # Pagination
            page = int(filters.get('page', 1))
            page_size = min(int(filters.get('page_size', 50)), 100)  # Max 100 per page
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            
            logs = queryset[start_index:end_index]
            total_count = queryset.count()
            total_pages = (total_count + page_size - 1) // page_size
            
            return {
                'success': True,
                'logs': [log.to_dict() for log in logs],
                'total_count': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages
            }
        
        except Exception as e:
            return BaseService.handle_exception('search_logs', e)
    
    @staticmethod
    def generate_audit_report(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate audit report for a period"""
        try:
            logs = ComplianceAuditLog.objects.filter(
                created_at__range=[start_date, end_date]
            )
            
            # Group by action type
            actions_summary = logs.values('action').annotate(count=models.Count('id')).order_by('-count')
            
            # Group by user
            users_summary = logs.values('user_email').annotate(count=models.Count('id')).order_by('-count')[:10]
            
            # Group by entity type
            entities_summary = logs.values('entity_type').annotate(count=models.Count('id')).order_by('-count')
            
            # Get top IP addresses
            ip_summary = logs.values('ip_address').annotate(count=models.Count('id')).order_by('-count')[:10]
            
            return {
                'success': True,
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'total_actions': logs.count(),
                'actions_summary': list(actions_summary),
                'top_users': list(users_summary),
                'entities_summary': list(entities_summary),
                'ip_summary': list(ip_summary),
                'message': 'Audit report generated'
            }
        
        except Exception as e:
            return BaseService.handle_exception('generate_audit_report', e)


class AlertService(BaseService):
    """Service for compliance alerts"""
    
    @staticmethod
    def create_alert(alert_type: str, severity: str, title: str, description: str, **kwargs) -> Optional[ComplianceAlert]:
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
                assigned_to=kwargs.get('assigned_to'),
                alert_data=kwargs.get('alert_data', {}),
                trigger_conditions=kwargs.get('trigger_conditions', {}),
                source=kwargs.get('source', 'system'),
                expires_at=kwargs.get('expires_at', timezone.now() + timedelta(hours=24)),
                priority=kwargs.get('priority', 'medium')
            )
            
            logger.info(f"Alert created: {alert_type} - {title} (Severity: {severity})")
            
            # Send real-time notification if configured
            if kwargs.get('send_notification', True):
                AlertService._send_real_time_notification(alert)
            
            return alert
        
        except Exception as e:
            logger.error(f"Error creating alert: {e}", exc_info=True)
            return None
    
    @staticmethod
    def _send_real_time_notification(alert: ComplianceAlert):
        """Send real-time notification for alert"""
        # This would integrate with websockets or push notification service
        try:
            # For now, log the notification
            logger.info(f"Real-time notification for alert {alert.alert_id}: {alert.title} (Severity: {alert.severity})")
            
            # You would integrate with your notification system here
            # Example: send_websocket_notification(alert.user_id, alert.to_dict())
        except Exception as e:
            logger.error(f"Error sending real-time notification: {e}")
    
    @staticmethod
    def get_active_alerts(**filters) -> Dict[str, Any]:
        """Get active alerts with filters"""
        try:
            queryset = ComplianceAlert.objects.filter(
                is_resolved=False,
                expires_at__gt=timezone.now()
            )
            
            # Apply filters
            if filters.get('severity'):
                queryset = queryset.filter(severity=filters['severity'])
            
            if filters.get('alert_type'):
                queryset = queryset.filter(alert_type=filters['alert_type'])
            
            if filters.get('assigned_to'):
                queryset = queryset.filter(assigned_to=filters['assigned_to'])
            
            if filters.get('user_id'):
                queryset = queryset.filter(user_id=filters['user_id'])
            
            if filters.get('compliance_request_id'):
                queryset = queryset.filter(compliance_request_id=filters['compliance_request_id'])
            
            if filters.get('kyc_verification_id'):
                queryset = queryset.filter(kyc_verification_id=filters['kyc_verification_id'])
            
            # Order by priority and creation date
            severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
            alerts = sorted(
                queryset,
                key=lambda x: (severity_order.get(x.severity, 5), -x.created_at.timestamp())
            )
            
            return {
                'success': True,
                'alerts': [alert.to_dict() for alert in alerts],
                'total_count': len(alerts)
            }
        
        except Exception as e:
            return BaseService.handle_exception('get_active_alerts', e)
    
    @staticmethod
    def resolve_alert(alert: ComplianceAlert, resolved_by: 'User', resolution_notes: str = '') -> Dict[str, Any]:
        """Resolve a compliance alert"""
        try:
            alert.is_resolved = True
            alert.resolved_by = resolved_by
            alert.resolved_at = timezone.now()
            alert.resolution_notes = resolution_notes
            alert.save()
            
            # Log resolution
            AuditService.log_action(
                user=resolved_by,
                action=f'Alert resolved: {alert.alert_id}',
                entity_type='compliance_alert',
                entity_id=alert.alert_id,
                new_value={
                    'is_resolved': True,
                    'resolved_by': resolved_by.email,
                    'resolved_at': timezone.now().isoformat(),
                    'resolution_notes': resolution_notes
                }
            )
            
            return {
                'success': True,
                'alert_id': alert.alert_id,
                'resolved_at': alert.resolved_at.isoformat(),
                'resolved_by': resolved_by.email,
                'message': 'Alert resolved successfully'
            }
        
        except Exception as e:
            return BaseService.handle_exception('resolve_alert', e, resolved_by)
    
    @staticmethod
    def assign_alert(alert: ComplianceAlert, assigned_to: 'User', assigned_by: 'User') -> Dict[str, Any]:
        """Assign an alert to a user"""
        try:
            old_assignee = alert.assigned_to
            alert.assigned_to = assigned_to
            alert.assigned_at = timezone.now()
            alert.assigned_by = assigned_by
            alert.save()
            
            # Log assignment
            AuditService.log_action(
                user=assigned_by,
                action=f'Alert assigned: {alert.alert_id}',
                entity_type='compliance_alert',
                entity_id=alert.alert_id,
                old_value={'assigned_to': old_assignee.email if old_assignee else None},
                new_value={
                    'assigned_to': assigned_to.email,
                    'assigned_by': assigned_by.email,
                    'assigned_at': timezone.now().isoformat()
                }
            )
            
            return {
                'success': True,
                'alert_id': alert.alert_id,
                'assigned_to': assigned_to.email,
                'assigned_at': alert.assigned_at.isoformat(),
                'assigned_by': assigned_by.email,
                'message': 'Alert assigned successfully'
            }
        
        except Exception as e:
            return BaseService.handle_exception('assign_alert', e, assigned_by)
    
    @staticmethod
    def cleanup_expired_alerts() -> int:
        """Clean up expired alerts"""
        try:
            expired_alerts = ComplianceAlert.objects.filter(
                expires_at__lt=timezone.now(),
                is_resolved=False
            )
            
            expired_count = expired_alerts.count()
            
            # Update expired alerts
            expired_alerts.update(
                is_resolved=True,
                resolution_notes='Expired automatically',
                resolved_at=timezone.now()
            )
            
            logger.info(f"Cleaned up {expired_count} expired alerts")
            return expired_count
        
        except Exception as e:
            logger.error(f"Error cleaning up alerts: {e}", exc_info=True)
            return 0


class ScheduledTasksService(BaseService):
    """Service for scheduled compliance tasks"""
    
    @staticmethod
    def cleanup_expired_tacs() -> int:
        """Clean up expired TAC codes"""
        try:
            expired_tacs = TACRequest.objects.filter(
                expires_at__lt=timezone.now(),
                is_used=False,
                is_expired=False
            )
            
            expired_count = expired_tacs.count()
            expired_tacs.update(is_expired=True)
            
            logger.info(f"Cleaned up {expired_count} expired TAC codes")
            return expired_count
        
        except Exception as e:
            logger.error(f"Error cleaning up TAC codes: {e}", exc_info=True)
            return 0
    
    @staticmethod
    def check_kyc_expirations() -> int:
        """Check for expiring KYC verifications"""
        try:
            expiry_threshold = timezone.now() + timedelta(days=30)
            expiring_kyc = KYCVerification.objects.filter(
                next_review_date__lte=expiry_threshold,
                verification_status='approved',
                is_expired=False
            )
            
            for kyc in expiring_kyc:
                # Calculate days until expiry
                days_until_expiry = (kyc.next_review_date - timezone.now()).days
                
                AlertService.create_alert(
                    alert_type='kyc_expiring',
                    severity='warning' if days_until_expiry > 7 else 'critical',
                    title=f"KYC expiring soon: {kyc.kyc_id}",
                    description=f"KYC for {kyc.full_name()} expires in {days_until_expiry} days",
                    kyc_verification=kyc,
                    user=kyc.user,
                    alert_data={
                        'expiry_date': kyc.next_review_date.isoformat(),
                        'days_until_expiry': days_until_expiry,
                        'kyc_id': kyc.kyc_id
                    }
                )
            
            logger.info(f"Checked {expiring_kyc.count()} expiring KYC verifications")
            return expiring_kyc.count()
        
        except Exception as e:
            logger.error(f"Error checking KYC expirations: {e}", exc_info=True)
            return 0
    
    @staticmethod
    def expire_kyc_verifications() -> int:
        """Expire KYC verifications that are past their review date"""
        try:
            expired_kyc = KYCVerification.objects.filter(
                next_review_date__lt=timezone.now(),
                verification_status='approved',
                is_expired=False
            )
            
            expired_count = 0
            for kyc in expired_kyc:
                kyc.verification_status = 'expired'
                kyc.is_expired = True
                kyc.expired_at = timezone.now()
                kyc.save()
                
                # Update user profile
                profile = getattr(kyc.user, 'compliance_profile', None)
                if profile:
                    profile.kyc_verified = False
                    profile.compliance_status = 'expired'
                    profile.save()
                
                # Create alert
                AlertService.create_alert(
                    alert_type='kyc_expired',
                    severity='critical',
                    title=f"KYC expired: {kyc.kyc_id}",
                    description=f"KYC for {kyc.full_name()} has expired",
                    kyc_verification=kyc,
                    user=kyc.user
                )
                
                expired_count += 1
            
            logger.info(f"Expired {expired_count} KYC verifications")
            return expired_count
        
        except Exception as e:
            logger.error(f"Error expiring KYC verifications: {e}", exc_info=True)
            return 0
    
    @staticmethod
    def generate_daily_stats() -> Dict[str, Any]:
        """Generate daily compliance statistics"""
        try:
            today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            yesterday_start = today_start - timedelta(days=1)
            
            # Calculate stats for compliance requests
            requests_stats = ComplianceRequest.objects.filter(
                created_at__range=[yesterday_start, today_start]
            ).aggregate(
                total=models.Count('id'),
                approved=models.Count('id', filter=models.Q(status='approved')),
                rejected=models.Count('id', filter=models.Q(status='rejected')),
                pending=models.Count('id', filter=models.Q(status='pending')),
                under_review=models.Count('id', filter=models.Q(status='under_review')),
                info_required=models.Count('id', filter=models.Q(status='info_required')),
                high_risk=models.Count('id', filter=models.Q(risk_level='high')),
                medium_risk=models.Count('id', filter=models.Q(risk_level='medium')),
                low_risk=models.Count('id', filter=models.Q(risk_level='low'))
            )
            
            # Calculate stats for KYC
            kyc_stats = KYCVerification.objects.filter(
                created_at__range=[yesterday_start, today_start]
            ).aggregate(
                total=models.Count('id'),
                approved=models.Count('id', filter=models.Q(verification_status='approved')),
                pending=models.Count('id', filter=models.Q(verification_status='pending')),
                rejected=models.Count('id', filter=models.Q(verification_status='rejected')),
                expired=models.Count('id', filter=models.Q(verification_status='expired'))
            )
            
            # Calculate stats for TAC
            tac_stats = TACRequest.objects.filter(
                created_at__range=[yesterday_start, today_start]
            ).aggregate(
                total=models.Count('id'),
                verified=models.Count('id', filter=models.Q(is_used=True)),
                expired=models.Count('id', filter=models.Q(is_expired=True)),
                pending=models.Count('id', filter=models.Q(is_used=False, is_expired=False))
            )
            
            # Calculate average processing time for approved requests
            approved_requests = ComplianceRequest.objects.filter(
                status='approved',
                created_at__range=[yesterday_start, today_start],
                resolved_at__isnull=False
            )
            
            avg_processing_time = None
            if approved_requests.exists():
                total_seconds = sum(
                    (req.resolved_at - req.created_at).total_seconds()
                    for req in approved_requests
                )
                avg_processing_time = total_seconds / approved_requests.count()
            
            stats = {
                'period_type': 'daily',
                'period_start': yesterday_start.isoformat(),
                'period_end': today_start.isoformat(),
                'compliance_requests': requests_stats,
                'kyc_verifications': kyc_stats,
                'tac_operations': tac_stats,
                'video_calls_scheduled': VideoCallSession.objects.filter(
                    created_at__range=[yesterday_start, today_start]
                ).count(),
                'alerts_generated': ComplianceAlert.objects.filter(
                    created_at__range=[yesterday_start, today_start]
                ).count(),
                'avg_processing_time_seconds': avg_processing_time,
                'top_request_types': list(
                    ComplianceRequest.objects.filter(
                        created_at__range=[yesterday_start, today_start]
                    ).values('request_type').annotate(
                        count=models.Count('id')
                    ).order_by('-count')[:5]
                )
            }
            
            logger.info(f"Generated daily stats: {stats}")
            
            # Store stats for reporting
            return {
                'success': True,
                'stats': stats,
                'generated_at': timezone.now().isoformat(),
                'message': 'Daily statistics generated'
            }
        
        except Exception as e:
            logger.error(f"Error generating daily stats: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def generate_weekly_report() -> Dict[str, Any]:
        """Generate weekly compliance report"""
        try:
            end_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            start_date = end_date - timedelta(days=7)
            
            # Get daily stats for the week
            daily_stats = []
            for i in range(7):
                day_start = start_date + timedelta(days=i)
                day_end = day_start + timedelta(days=1)
                
                day_stats = {
                    'date': day_start.date().isoformat(),
                    'requests': ComplianceRequest.objects.filter(
                        created_at__range=[day_start, day_end]
                    ).count(),
                    'approved': ComplianceRequest.objects.filter(
                        created_at__range=[day_start, day_end],
                        status='approved'
                    ).count(),
                    'kyc_submissions': KYCVerification.objects.filter(
                        created_at__range=[day_start, day_end]
                    ).count(),
                    'kyc_approved': KYCVerification.objects.filter(
                        created_at__range=[day_start, day_end],
                        verification_status='approved'
                    ).count(),
                    'tac_generated': TACRequest.objects.filter(
                        created_at__range=[day_start, day_end]
                    ).count(),
                }
                daily_stats.append(day_stats)
            
            # Calculate weekly totals
            weekly_stats = {
                'period_start': start_date.isoformat(),
                'period_end': end_date.isoformat(),
                'total_requests': ComplianceRequest.objects.filter(
                    created_at__range=[start_date, end_date]
                ).count(),
                'total_approved': ComplianceRequest.objects.filter(
                    created_at__range=[start_date, end_date],
                    status='approved'
                ).count(),
                'approval_rate': 0,
                'total_kyc': KYCVerification.objects.filter(
                    created_at__range=[start_date, end_date]
                ).count(),
                'kyc_approval_rate': 0,
                'total_tac': TACRequest.objects.filter(
                    created_at__range=[start_date, end_date]
                ).count(),
                'tac_verification_rate': 0,
                'daily_stats': daily_stats
            }
            
            # Calculate rates
            if weekly_stats['total_requests'] > 0:
                weekly_stats['approval_rate'] = round(
                    (weekly_stats['total_approved'] / weekly_stats['total_requests']) * 100, 2
                )
            
            kyc_approved = KYCVerification.objects.filter(
                created_at__range=[start_date, end_date],
                verification_status='approved'
            ).count()
            
            if weekly_stats['total_kyc'] > 0:
                weekly_stats['kyc_approval_rate'] = round((kyc_approved / weekly_stats['total_kyc']) * 100, 2)
            
            tac_verified = TACRequest.objects.filter(
                created_at__range=[start_date, end_date],
                is_used=True
            ).count()
            
            if weekly_stats['total_tac'] > 0:
                weekly_stats['tac_verification_rate'] = round((tac_verified / weekly_stats['total_tac']) * 100, 2)
            
            logger.info(f"Generated weekly report: {weekly_stats}")
            
            return {
                'success': True,
                'report': weekly_stats,
                'generated_at': timezone.now().isoformat(),
                'message': 'Weekly report generated'
            }
        
        except Exception as e:
            logger.error(f"Error generating weekly report: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def cleanup_old_audit_logs(days_to_keep: int = 90) -> int:
        """Clean up audit logs older than specified days"""
        try:
            cutoff_date = timezone.now() - timedelta(days=days_to_keep)
            old_logs = ComplianceAuditLog.objects.filter(created_at__lt=cutoff_date)
            
            deleted_count = old_logs.count()
            old_logs.delete()
            
            logger.info(f"Cleaned up {deleted_count} audit logs older than {days_to_keep} days")
            return deleted_count
        
        except Exception as e:
            logger.error(f"Error cleaning up audit logs: {e}", exc_info=True)
            return 0