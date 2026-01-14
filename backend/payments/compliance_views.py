# payments/compliance_views.py - UPDATED TO USE CENTRAL COMPLIANCE

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status
import logging

from .compliance_services import ComplianceIntegrationService
from .serializers import (
    ManualPaymentRequestSerializer,
    TACVerificationSerializer,
    KYCFormSubmitSerializer,
    AdminReleasePaymentSerializer,
    ScheduleVideoCallSerializer,
    CompleteVideoCallSerializer
)

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_manual_payment(request):
    """User requests a manual payment (now calls compliance app)"""
    serializer = ManualPaymentRequestSerializer(data=request.data)
    if serializer.is_valid():
        try:
            result = ComplianceIntegrationService.request_manual_payment_approval(
                user=request.user,
                amount=serializer.validated_data['amount'],
                currency=serializer.validated_data.get('currency', 'USD'),
                description=serializer.validated_data.get('description', '')
            )
            
            if result['success']:
                return Response(result, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'error': result.get('error', 'Request failed')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_tac(request):
    """User verifies TAC code (calls compliance app)"""
    serializer = TACVerificationSerializer(data=request.data)
    if serializer.is_valid():
        try:
            # In this new system, we need compliance_id instead of reference_code
            # For backward compatibility, we might need to map reference_code to compliance_id
            compliance_id = serializer.validated_data.get('compliance_id')
            
            if not compliance_id:
                return Response(
                    {'error': 'compliance_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            result = ComplianceIntegrationService.verify_tac_code(
                compliance_id=compliance_id,
                tac_code=serializer.validated_data['tac_code'],
                user=request.user
            )
            
            if result['success']:
                return Response(result)
            else:
                return Response(
                    {'error': result.get('error', 'TAC verification failed')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_kyc_form(request):
    """User submits KYC form (calls compliance app)"""
    serializer = KYCFormSubmitSerializer(data=request.data)
    if serializer.is_valid():
        try:
            result = ComplianceIntegrationService.submit_kyc_form(
                compliance_id=serializer.validated_data['compliance_id'],
                form_data=serializer.validated_data['form_data'],
                documents=serializer.validated_data.get('documents', [])
            )
            
            if result['success']:
                return Response(result)
            else:
                return Response(
                    {'error': result.get('error', 'KYC submission failed')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ADMIN ENDPOINTS

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_compliance_dashboard(request):
    """Admin dashboard showing pending compliance requests"""
    try:
        result = ComplianceIntegrationService.get_pending_approvals()
        
        if result['success']:
            return Response(result)
        else:
            return Response(
                {'error': result.get('error', 'Failed to load dashboard')},
                status=status.HTTP_400_BAD_REQUEST
            )
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_generate_tac(request):
    """Admin generates TAC for approved payment"""
    serializer = AdminReleasePaymentSerializer(data=request.data)
    if serializer.is_valid():
        try:
            result = ComplianceIntegrationService.generate_tac_for_transaction(
                compliance_id=serializer.validated_data['compliance_id'],
                admin_user=request.user
            )
            
            if result['success']:
                return Response(result)
            else:
                return Response(
                    {'error': result.get('error', 'TAC generation failed')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_schedule_video_call(request):
    """Admin schedules video call (calls compliance app)"""
    serializer = ScheduleVideoCallSerializer(data=request.data)
    if serializer.is_valid():
        try:
            result = ComplianceIntegrationService.schedule_video_call(
                compliance_id=serializer.validated_data['compliance_id'],
                call_datetime=serializer.validated_data['call_datetime'],
                call_link=serializer.validated_data['call_link'],
                admin_user=request.user
            )
            
            if result['success']:
                return Response(result)
            else:
                return Response(
                    {'error': result.get('error', 'Scheduling failed')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_complete_video_call(request):
    """Admin completes video call verification"""
    serializer = CompleteVideoCallSerializer(data=request.data)
    if serializer.is_valid():
        try:
            result = ComplianceIntegrationService.complete_video_call(
                compliance_id=serializer.validated_data['compliance_id'],
                approved=serializer.validated_data['approved'],
                admin_notes=serializer.validated_data.get('admin_notes', '')
            )
            
            if result['success']:
                return Response(result)
            else:
                return Response(
                    {'error': result.get('error', 'Video call completion failed')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_approve_request(request):
    """Admin approves a compliance request"""
    compliance_id = request.data.get('compliance_id')
    notes = request.data.get('notes', '')
    
    if not compliance_id:
        return Response(
            {'error': 'compliance_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        result = ComplianceIntegrationService.approve_compliance_request(
            compliance_id=compliance_id,
            admin_user=request.user,
            notes=notes
        )
        
        if result['success']:
            return Response(result)
        else:
            return Response(
                {'error': result.get('error', 'Approval failed')},
                status=status.HTTP_400_BAD_REQUEST
            )
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_reject_request(request):
    """Admin rejects a compliance request"""
    compliance_id = request.data.get('compliance_id')
    reason = request.data.get('reason', '')
    
    if not compliance_id:
        return Response(
            {'error': 'compliance_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        result = ComplianceIntegrationService.reject_compliance_request(
            compliance_id=compliance_id,
            admin_user=request.user,
            reason=reason
        )
        
        if result['success']:
            return Response(result)
        else:
            return Response(
                {'error': result.get('error', 'Rejection failed')},
                status=status.HTTP_400_BAD_REQUEST
            )
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_compliance_status(request):
    """User checks their compliance status"""
    try:
        # Get user's transactions with compliance requirements
        transactions = request.user.transactions.filter(
            status__in=['pending_compliance', 'compliance_approved']
        ).select_related('account').order_by('-created_at')[:10]
        
        transaction_data = []
        for transaction in transactions:
            status_info = {'status': transaction.status}
            
            # If we have a compliance reference, get detailed status
            if transaction.compliance_reference:
                result = ComplianceIntegrationService.get_compliance_status(
                    transaction.compliance_reference
                )
                
                if result.get('success'):
                    status_info['compliance_details'] = result.get('data', {})
            
            transaction_data.append({
                'transaction_id': transaction.transaction_id,
                'amount': str(transaction.amount),
                'currency': transaction.currency,
                'description': transaction.description,
                'created_at': transaction.created_at,
                **status_info
            })
        
        return Response({
            'pending_compliance': transaction_data,
            'total_pending': len(transaction_data)
        })
        
    except Exception as e:
        logger.error(f"User compliance status failed: {str(e)}")
        return Response(
            {'error': 'Failed to load compliance status'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )