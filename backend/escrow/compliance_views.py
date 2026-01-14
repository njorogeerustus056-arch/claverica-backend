# escrow/compliance_views.py - COMPLIANCE INTEGRATION VIEWS

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status
import logging

from .compliance_services import EscrowComplianceService
from .serializers import (
    EscrowDisputeRequestSerializer,
    EscrowTACVerificationSerializer,
    EscrowComplianceFormSerializer,
    ManualReleaseRequestSerializer
)
from .models import Escrow

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_dispute_resolution(request, escrow_id):
    """Request compliance intervention for escrow dispute"""
    try:
        escrow = Escrow.objects.get(id=escrow_id)
        
        # Check if user is involved in escrow
        user_id = str(request.user.id)
        if user_id != escrow.sender_id and user_id != escrow.receiver_id:
            return Response(
                {"error": "Unauthorized to dispute this escrow"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = EscrowDisputeRequestSerializer(data=request.data)
        if serializer.is_valid():
            result = EscrowComplianceService.request_dispute_resolution(
                escrow=escrow,
                user=request.user,
                reason=serializer.validated_data['reason'],
                dispute_details=serializer.validated_data.get('details')
            )
            
            if result['success']:
                return Response(result, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'error': result.get('error', 'Dispute resolution request failed')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Escrow.DoesNotExist:
        return Response({"error": "Escrow not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_kyc_verification(request, escrow_id):
    """Request KYC verification for high-value escrow"""
    try:
        escrow = Escrow.objects.get(id=escrow_id)
        
        # Check if user is the sender (only sender can request KYC for high-value)
        user_id = str(request.user.id)
        if user_id != escrow.sender_id:
            return Response(
                {"error": "Only the sender can request KYC verification"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if escrow requires KYC (high value)
        if escrow.amount < 10000:
            return Response(
                {"error": "KYC verification only required for escrows over $10,000"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = EscrowComplianceService.request_kyc_for_high_value(
            escrow=escrow,
            user=request.user
        )
        
        if result['success']:
            return Response(result)
        else:
            return Response(
                {'error': result.get('error', 'KYC request failed')},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Escrow.DoesNotExist:
        return Response({"error": "Escrow not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_tac_for_release(request, escrow_id):
    """Verify TAC code for compliance-approved escrow release"""
    try:
        escrow = Escrow.objects.get(id=escrow_id)
        
        # Check if user is authorized
        user_id = str(request.user.id)
        if user_id != escrow.sender_id and user_id != escrow.receiver_id:
            return Response(
                {"error": "Unauthorized to release this escrow"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = EscrowTACVerificationSerializer(data=request.data)
        if serializer.is_valid():
            if not escrow.compliance_reference:
                return Response(
                    {"error": "No compliance reference found for this escrow"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            result = EscrowComplianceService.verify_tac_for_release(
                compliance_id=escrow.compliance_reference,
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
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Escrow.DoesNotExist:
        return Response({"error": "Escrow not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_compliance_form(request, escrow_id):
    """Submit compliance form for escrow dispute"""
    try:
        escrow = Escrow.objects.get(id=escrow_id)
        
        # Check if user is involved
        user_id = str(request.user.id)
        if user_id != escrow.sender_id and user_id != escrow.receiver_id:
            return Response(
                {"error": "Unauthorized to submit form for this escrow"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = EscrowComplianceFormSerializer(data=request.data)
        if serializer.is_valid():
            if not escrow.compliance_reference:
                return Response(
                    {"error": "No compliance reference found for this escrow"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            result = EscrowComplianceService.submit_compliance_form(
                compliance_id=escrow.compliance_reference,
                form_data=serializer.validated_data['form_data'],
                user=request.user
            )
            
            if result['success']:
                return Response(result)
            else:
                return Response(
                    {'error': result.get('error', 'Form submission failed')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Escrow.DoesNotExist:
        return Response({"error": "Escrow not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_manual_release_approval(request, escrow_id):
    """Request manual release approval for special cases"""
    try:
        escrow = Escrow.objects.get(id=escrow_id)
        
        # Check if user is authorized (sender or receiver)
        user_id = str(request.user.id)
        if user_id != escrow.sender_id and user_id != escrow.receiver_id:
            return Response(
                {"error": "Unauthorized to request manual release"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ManualReleaseRequestSerializer(data=request.data)
        if serializer.is_valid():
            result = EscrowComplianceService.request_manual_release_approval(
                escrow=escrow,
                user=request.user,
                reason=serializer.validated_data['reason']
            )
            
            if result['success']:
                return Response(result, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'error': result.get('error', 'Manual release request failed')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Escrow.DoesNotExist:
        return Response({"error": "Escrow not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_escrow_compliance_status(request, escrow_id):
    """Get compliance status for an escrow"""
    try:
        escrow = Escrow.objects.get(id=escrow_id)
        
        # Check if user is involved
        user_id = str(request.user.id)
        if user_id != escrow.sender_id and user_id != escrow.receiver_id:
            return Response(
                {"error": "Unauthorized to view compliance status"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not escrow.compliance_reference:
            return Response({
                'has_compliance_request': False,
                'message': 'No compliance request for this escrow'
            })
        
        result = EscrowComplianceService.get_compliance_status(
            escrow.compliance_reference
        )
        
        if result['success']:
            return Response({
                'has_compliance_request': True,
                'compliance_reference': escrow.compliance_reference,
                'status': result.get('data', {}).get('status', 'unknown'),
                'details': result.get('data', {})
            })
        else:
            return Response({
                'has_compliance_request': True,
                'compliance_reference': escrow.compliance_reference,
                'status': 'error',
                'error': result.get('error', 'Failed to fetch status')
            })
            
    except Escrow.DoesNotExist:
        return Response({"error": "Escrow not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ADMIN ENDPOINTS

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_escrow_compliance_dashboard(request):
    """Admin dashboard for escrow compliance requests"""
    try:
        result = EscrowComplianceService.get_pending_compliance_requests()
        
        if result['success']:
            return Response(result)
        else:
            return Response(
                {'error': result.get('error', 'Failed to load dashboard')},
                status=status.HTTP_400_BAD_REQUEST
            )
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)