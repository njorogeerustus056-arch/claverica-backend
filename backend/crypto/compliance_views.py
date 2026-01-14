# crypto/views/compliance_views.py - COMPLIANCE INTEGRATION VIEWS

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from django.utils import timezone
from decimal import Decimal
import logging

from ..models import CryptoTransaction, CryptoWallet, CryptoComplianceFlag, CryptoAuditLog
from ..services.compliance_service import CryptoComplianceService
from ..serializers import (
    CryptoTransactionSerializer,
    CryptoComplianceFlagSerializer,
    TACVerificationSerializer,
    KYCRequestSerializer,
    ScheduleVideoCallSerializer,
    ComplianceRequestSerializer,
    CryptoAuditLogSerializer
)

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_crypto_kyc_view(request):
    """
    Request KYC verification for a crypto transaction
    """
    serializer = KYCRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    
    transaction_id = serializer.validated_data['transaction_id']
    transaction = get_object_or_404(CryptoTransaction, id=transaction_id, user=request.user)
    
    if transaction.compliance_status == 'approved':
        return Response({'error': 'Compliance already approved'}, status=400)
    
    # Request KYC from central compliance system
    result = CryptoComplianceService.request_kyc_for_transaction(
        transaction_id=transaction.id,
        user_id=request.user.id,
        amount=transaction.amount_usd or transaction.amount,
        currency='USD',
        reason=serializer.validated_data.get('reason', '')
    )
    
    if result['success']:
        transaction.compliance_reference = result['compliance_reference']
        transaction.compliance_status = 'pending'
        transaction.requires_compliance_approval = True
        if transaction.status == 'pending':
            transaction.status = 'pending_compliance'
        transaction.save()
        
        # Create audit log
        CryptoAuditLog.objects.create(
            user=request.user,
            action='compliance_requested',
            transaction=transaction,
            details={
                'compliance_reference': result['compliance_reference'],
                'reason': serializer.validated_data.get('reason', ''),
                'amount': str(transaction.amount_usd or transaction.amount)
            }
        )
        
        return Response({
            'success': True,
            'message': 'KYC verification requested',
            'compliance_reference': result['compliance_reference'],
            'requires_action': result.get('requires_action', False),
            'transaction': CryptoTransactionSerializer(transaction).data
        })
    
    return Response({'error': 'Failed to request KYC verification'}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_crypto_tac_view(request):
    """
    Verify TAC for crypto transaction
    """
    serializer = TACVerificationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    
    compliance_reference = serializer.validated_data['compliance_reference']
    tac_code = serializer.validated_data['tac_code']
    
    # Find transaction by compliance reference
    transaction = CryptoTransaction.objects.filter(
        compliance_reference=compliance_reference,
        user=request.user
    ).first()
    
    if not transaction:
        return Response({'error': 'Transaction not found'}, status=404)
    
    # Verify TAC with central compliance system
    result = CryptoComplianceService.verify_tac_code(
        compliance_reference=compliance_reference,
        tac_code=tac_code,
        user_id=request.user.id
    )
    
    if result.get('success') and result.get('valid'):
        # Update transaction status
        transaction.compliance_status = 'approved'
        transaction.requires_compliance_approval = False
        
        # If TAC verified, mark as compliance approved
        if transaction.status == 'pending_compliance':
            transaction.status = 'compliance_approved'
        
        transaction.save()
        
        # Create audit log
        CryptoAuditLog.objects.create(
            user=request.user,
            action='tac_verified',
            transaction=transaction,
            details={
                'compliance_reference': compliance_reference,
                'method': 'tac_verification'
            }
        )
        
        return Response({
            'success': True,
            'message': 'TAC verified successfully',
            'transaction': CryptoTransactionSerializer(transaction).data
        })
    
    return Response({
        'success': False,
        'error': result.get('error', 'Invalid TAC code')
    }, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def crypto_compliance_status_view(request, transaction_id):
    """
    Check compliance status for crypto transaction
    """
    transaction = get_object_or_404(CryptoTransaction, id=transaction_id, user=request.user)
    
    if not transaction.compliance_reference:
        return Response({'status': 'not_required', 'approved': True})
    
    # Check status from central compliance system
    status_data = CryptoComplianceService.check_compliance_status(
        transaction.compliance_reference
    )
    
    # Update local status if changed
    if status_data.get('status') != transaction.compliance_status:
        transaction.compliance_status = status_data.get('status')
        
        # Update transaction status based on compliance decision
        if status_data.get('status') == 'approved':
            transaction.requires_compliance_approval = False
            if transaction.status == 'pending_compliance':
                transaction.status = 'compliance_approved'
        elif status_data.get('status') == 'rejected':
            transaction.status = 'compliance_rejected'
        
        transaction.save()
    
    return Response({
        'transaction_id': str(transaction.id),
        'compliance_reference': transaction.compliance_reference,
        'compliance_status': transaction.compliance_status,
        'requires_compliance_approval': transaction.requires_compliance_approval,
        'transaction_status': transaction.status,
        'details': status_data,
        'updated_at': transaction.updated_at
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def flag_suspicious_crypto_view(request):
    """
    Flag suspicious crypto activity (admin/automated)
    """
    serializer = ComplianceRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    
    transaction_id = serializer.validated_data['transaction_id']
    reason = serializer.validated_data.get('reason', 'Suspicious pattern detected')
    indicators = serializer.validated_data.get('indicators', [])
    
    transaction = get_object_or_404(CryptoTransaction, id=transaction_id)
    
    # Flag in central compliance system
    result = CryptoComplianceService.flag_suspicious_transaction(
        transaction_id=transaction.id,
        user_id=transaction.user.id,
        indicators=indicators,
        reason=reason
    )
    
    if result['success']:
        # Update local transaction
        transaction.compliance_reference = result['compliance_reference']
        transaction.compliance_status = 'flagged'
        transaction.is_suspicious = True
        transaction.requires_compliance_approval = True
        if transaction.status == 'pending':
            transaction.status = 'pending_compliance'
        transaction.save()
        
        # Create compliance flag record
        flag = CryptoComplianceFlag.objects.create(
            transaction=transaction,
            flag_type='suspicious_pattern',
            priority='high',
            description=reason,
            indicators={'indicators': indicators}
        )
        
        # Create audit log
        CryptoAuditLog.objects.create(
            user=request.user,
            action='flag_created',
            transaction=transaction,
            details={
                'flag_id': str(flag.id),
                'reason': reason,
                'indicators': indicators
            }
        )
        
        return Response({
            'success': True,
            'message': 'Transaction flagged for compliance review',
            'compliance_reference': result['compliance_reference'],
            'flag_id': str(flag.id)
        })
    
    return Response({'error': 'Failed to flag transaction'}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def schedule_video_verification_view(request):
    """
    Schedule video verification for crypto transaction
    """
    serializer = ScheduleVideoCallSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    
    compliance_reference = serializer.validated_data['compliance_reference']
    preferred_time = serializer.validated_data['preferred_time']
    timezone = serializer.validated_data.get('timezone', 'UTC')
    
    # Find transaction
    transaction = CryptoTransaction.objects.filter(
        compliance_reference=compliance_reference,
        user=request.user
    ).first()
    
    if not transaction:
        return Response({'error': 'Transaction not found'}, status=404)
    
    # Schedule video verification
    result = CryptoComplianceService.schedule_video_verification(
        compliance_reference=compliance_reference,
        user_id=request.user.id,
        preferred_time=preferred_time,
        timezone=timezone
    )
    
    if result.get('success'):
        # Create audit log
        CryptoAuditLog.objects.create(
            user=request.user,
            action='compliance_requested',
            transaction=transaction,
            details={
                'compliance_reference': compliance_reference,
                'scheduled_time': preferred_time.isoformat(),
                'timezone': timezone
            }
        )
        
        return Response({
            'success': True,
            'message': 'Video verification scheduled',
            'scheduled_time': result.get('scheduled_time'),
            'meeting_link': result.get('meeting_link')
        })
    
    return Response({
        'success': False,
        'error': result.get('error', 'Failed to schedule video verification')
    }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_crypto_compliance_dashboard(request):
    """
    Get crypto compliance dashboard data
    """
    user = request.user
    
    # Get pending compliance requests
    pending_transactions = CryptoTransaction.objects.filter(
        user=user,
        requires_compliance_approval=True,
        compliance_status__in=['pending', 'flagged', 'under_review']
    ).order_by('-created_at')
    
    # Get recent compliance history
    compliance_history = CryptoTransaction.objects.filter(
        user=user,
        compliance_reference__isnull=False
    ).exclude(compliance_status='not_required').order_by('-updated_at')[:10]
    
    # Get compliance flags
    compliance_flags = CryptoComplianceFlag.objects.filter(
        transaction__user=user,
        is_resolved=False
    ).select_related('transaction').order_by('-created_at')
    
    # Get audit logs
    audit_logs = CryptoAuditLog.objects.filter(
        user=user,
        action__in=['compliance_requested', 'compliance_approved', 
                   'compliance_rejected', 'tac_verified']
    ).order_by('-created_at')[:20]
    
    return Response({
        'pending_requests': CryptoTransactionSerializer(pending_transactions, many=True).data,
        'compliance_history': CryptoTransactionSerializer(compliance_history, many=True).data,
        'compliance_flags': CryptoComplianceFlagSerializer(compliance_flags, many=True).data,
        'audit_logs': CryptoAuditLogSerializer(audit_logs, many=True).data,
        'stats': {
            'pending_count': pending_transactions.count(),
            'approved_count': CryptoTransaction.objects.filter(
                user=user, compliance_status='approved'
            ).count(),
            'rejected_count': CryptoTransaction.objects.filter(
                user=user, compliance_status='rejected'
            ).count(),
            'flagged_count': CryptoTransaction.objects.filter(
                user=user, compliance_status='flagged'
            ).count(),
            'total_compliance_requests': CryptoTransaction.objects.filter(
                user=user, compliance_reference__isnull=False
            ).count()
        }
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_approve_crypto_request(request):
    """
    Admin approves a crypto compliance request
    """
    compliance_reference = request.data.get('compliance_reference')
    notes = request.data.get('notes', '')
    
    if not compliance_reference:
        return Response({'error': 'compliance_reference is required'}, status=400)
    
    # Find transaction
    transaction = CryptoTransaction.objects.filter(
        compliance_reference=compliance_reference
    ).first()
    
    if not transaction:
        return Response({'error': 'Transaction not found'}, status=404)
    
    # Approve in central compliance system
    result = CryptoComplianceService.approve_compliance_request(
        compliance_reference=compliance_reference,
        admin_user_id=request.user.id,
        notes=notes
    )
    
    if result.get('success'):
        # Update local transaction
        transaction.mark_as_compliance_approved()
        
        # Create audit log
        CryptoAuditLog.objects.create(
            user=request.user,
            action='compliance_approved',
            transaction=transaction,
            details={
                'compliance_reference': compliance_reference,
                'admin_notes': notes
            }
        )
        
        return Response({
            'success': True,
            'message': 'Compliance request approved',
            'transaction': CryptoTransactionSerializer(transaction).data
        })
    
    return Response({
        'success': False,
        'error': result.get('error', 'Failed to approve request')
    }, status=500)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_reject_crypto_request(request):
    """
    Admin rejects a crypto compliance request
    """
    compliance_reference = request.data.get('compliance_reference')
    reason = request.data.get('reason', '')
    
    if not compliance_reference:
        return Response({'error': 'compliance_reference is required'}, status=400)
    
    # Find transaction
    transaction = CryptoTransaction.objects.filter(
        compliance_reference=compliance_reference
    ).first()
    
    if not transaction:
        return Response({'error': 'Transaction not found'}, status=404)
    
    # Reject in central compliance system
    result = CryptoComplianceService.reject_compliance_request(
        compliance_reference=compliance_reference,
        admin_user_id=request.user.id,
        reason=reason
    )
    
    if result.get('success'):
        # Update local transaction
        transaction.mark_as_compliance_rejected(reason)
        
        # Create audit log
        CryptoAuditLog.objects.create(
            user=request.user,
            action='compliance_rejected',
            transaction=transaction,
            details={
                'compliance_reference': compliance_reference,
                'reason': reason
            }
        )
        
        return Response({
            'success': True,
            'message': 'Compliance request rejected',
            'transaction': CryptoTransactionSerializer(transaction).data
        })
    
    return Response({
        'success': False,
        'error': result.get('error', 'Failed to reject request')
    }, status=500)