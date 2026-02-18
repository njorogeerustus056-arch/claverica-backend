"""
compliance/views.py - API endpoints for compliance with Pusher integration
"""
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import models

from .models import TransferRequest, TransferLog, ComplianceSetting
from .serializers import (
    TransferCreateSerializer, TransferSerializer, TransferDetailSerializer,
    TACVerificationSerializer, TransferStatusSerializer,
    TransferHistorySerializer, ComplianceSettingSerializer
)
from backend.utils.pusher import trigger_notification  #  ADDED

class TransferViewSet(viewsets.ModelViewSet):
    """API endpoint for transfer requests (client facing)"""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get transfers for authenticated user"""
        user = self.request.user
        return TransferRequest.objects.filter(account=user)

    def get_serializer_class(self):
        if self.action == 'create':
            return TransferCreateSerializer
        elif self.action == 'retrieve':
            return TransferDetailSerializer
        return TransferSerializer

    def perform_create(self, serializer):
        """Create a new transfer request"""
        user = self.request.user

        if not hasattr(user, 'account_number') or not user.account_number:
            raise ValidationError("User account is not fully set up - missing account number")

        data = serializer.validated_data
        transfer = serializer.save(
            account=user,
            status='pending_tac'
        )

        #  ADDED: Trigger Pusher event for transfer initiated
        trigger_notification(
            account_number=user.account_number,
            event_name='transfer.initiated',
            data={
                'id': transfer.id,
                'amount': float(transfer.amount),
                'recipient': transfer.recipient_name,
                'destination_type': transfer.destination_type,
                'status': 'pending_tac',
                'reference': transfer.reference,
                'created_at': transfer.created_at.isoformat()
            }
        )

        # Check KYC requirement
        try:
            from kyc.models import KYCDocument
            has_kyc = KYCDocument.objects.filter(
                user=user,
                status='approved'
            ).exists()

            if data['amount'] >= 1500.00 and not has_kyc:
                transfer.requires_kyc = True
                transfer.status = 'kyc_required'
                transfer.save()
                
                #  ADDED: Trigger Pusher for KYC requirement
                trigger_notification(
                    account_number=user.account_number,
                    event_name='kyc.pending',
                    data={
                        'transfer_id': transfer.id,
                        'amount': float(transfer.amount),
                        'message': 'KYC required for this transfer amount'
                    }
                )

        except ImportError:
            pass

        return

    #  FIX: Add url_path parameter for hyphenated URL
    @action(detail=True, methods=['post'], url_path='verify-tac')
    def verify_tac(self, request, pk=None):
        """Verify TAC code entered by client"""
        transfer = self.get_object()

        if transfer.status != 'tac_sent':
            return Response(
                {'error': 'TAC not sent yet'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = TACVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            tac_code = serializer.validated_data['tac_code']

            # Verify TAC
            if transfer.verify_tac(tac_code):
                #  ADDED: Trigger Pusher for TAC verified
                trigger_notification(
                    account_number=transfer.account.account_number,
                    event_name='transfer.tac_verified',
                    data={
                        'id': transfer.id,
                        'amount': float(transfer.amount),
                        'status': 'tac_verified',
                        'message': 'TAC verified successfully'
                    }
                )

                return Response({
                    'success': True,
                    'message': 'TAC verified successfully',
                    'status': transfer.status,
                    'next_step': 'Admin will process funds deduction'
                })
            else:
                return Response({
                    'error': 'Invalid or expired TAC code'
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get transfer status"""
        transfer = self.get_object()
        serializer = TransferStatusSerializer(transfer)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending transfers for user"""
        user = request.user

        if not hasattr(user, 'account_number') or not user.account_number:
            return Response(
                {'error': 'User account is not fully set up'},
                status=status.HTTP_400_BAD_REQUEST
            )

        pending_transfers = TransferRequest.objects.filter(
            account=user,
            status__in=['pending_tac', 'tac_generated', 'tac_sent', 'pending_settlement']
        ).order_by('-created_at')

        serializer = TransferSerializer(pending_transfers, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get transfer history for user"""
        user = request.user

        if not hasattr(user, 'account_number') or not user.account_number:
            return Response(
                {'error': 'User account is not fully set up'},
                status=status.HTTP_400_BAD_REQUEST
            )

        transfers = TransferRequest.objects.filter(
            account=user
        ).order_by('-created_at')

        serializer = TransferHistorySerializer(transfers, many=True)
        return Response(serializer.data)


class AdminTransferViewSet(viewsets.ModelViewSet):
    """API endpoint for admin transfer operations"""

    permission_classes = [IsAdminUser]
    queryset = TransferRequest.objects.all()
    serializer_class = TransferSerializer

    @action(detail=False, methods=['get'])
    def need_tac(self, request):
        """Get transfers needing TAC generation"""
        pending_transfers = TransferRequest.objects.filter(
            status='pending_tac'
        ).order_by('created_at')

        serializer = self.get_serializer(pending_transfers, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def need_settlement(self, request):
        """Get transfers needing settlement"""
        pending_settlements = TransferRequest.objects.filter(
            status='tac_verified'
        ).order_by('created_at')

        serializer = self.get_serializer(pending_settlements, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def generate_tac(self, request, pk=None):
        """Generate TAC for transfer (admin only)"""
        transfer = self.get_object()

        if transfer.status != 'pending_tac':
            return Response(
                {'error': 'Transfer not ready for TAC generation'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            tac_code = transfer.generate_tac(request.user)
            
            #  ADDED: Trigger Pusher for TAC sent
            trigger_notification(
                account_number=transfer.account.account_number,
                event_name='transfer.tac_sent',
                data={
                    'id': transfer.id,
                    'amount': float(transfer.amount),
                    'status': 'tac_sent',
                    'message': 'TAC code has been generated. Contact live agent for the code.',
                    'expires_at': transfer.tac_expires_at.isoformat() if transfer.tac_expires_at else None
                }
            )

            return Response({
                'success': True,
                'tac_code': tac_code,
                'message': 'TAC generated. Please send to client manually.',
                'client_email': transfer.account.email if transfer.account else 'No email',
                'transfer_reference': transfer.reference,
                'amount': transfer.amount,
                'expires_at': transfer.tac_expires_at
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        """Mark transfer as completed (after manual bank transfer)"""
        transfer = self.get_object()

        if transfer.status != 'tac_verified':
            return Response(
                {'error': 'Transfer must have verified TAC first'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            transfer.mark_for_settlement(request.user)
            transfer.mark_completed()

            #  ADDED: Trigger Pusher for transfer completed
            trigger_notification(
                account_number=transfer.account.account_number,
                event_name='transfer.completed',
                data={
                    'id': transfer.id,
                    'amount': float(transfer.amount),
                    'recipient': transfer.recipient_name,
                    'status': 'completed',
                    'reference': transfer.reference,
                    'message': 'Your transfer has been completed successfully'
                }
            )

            return Response({
                'success': True,
                'message': 'Transfer marked as completed',
                'transfer_reference': transfer.reference,
                'status': transfer.status
            })

        except Exception as e:
            #  ADDED: Trigger Pusher for transfer failed
            trigger_notification(
                account_number=transfer.account.account_number,
                event_name='transfer.failed',
                data={
                    'id': transfer.id,
                    'amount': float(transfer.amount),
                    'status': 'failed',
                    'reason': str(e),
                    'message': f'Transfer failed: {str(e)}'
                }
            )

            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class ComplianceSettingViewSet(viewsets.ModelViewSet):
    """API endpoint for compliance settings (admin only)"""

    permission_classes = [IsAdminUser]
    queryset = ComplianceSetting.objects.all()
    serializer_class = ComplianceSettingSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_kyc_requirement(request):
    """Check if KYC is required for a transfer amount"""
    amount = request.GET.get('amount', 0)

    try:
        amount = float(amount)
        requires_kyc = amount >= 1500.00

        return Response({
            'amount': amount,
            'requires_kyc': requires_kyc,
            'kyc_threshold': 1500.00,
            'message': 'KYC required for transfers >= $1,500' if requires_kyc else 'KYC not required'
        })

    except ValueError:
        return Response(
            {'error': 'Invalid amount'},
            status=status.HTTP_400_BAD_REQUEST
        )
