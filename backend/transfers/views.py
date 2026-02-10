"""
Transfer Views - API endpoints for transfer operations
"""

import logging
from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db import transaction
from django.shortcuts import get_object_or_404

from .models import Transfer, TAC, TransferLog, TransferLimit
from .serializers import (
    TransferCreateSerializer, TransferSerializer, TransferDetailSerializer,
    TACVerificationSerializer, TransferSettlementSerializer,
    TransferCancelSerializer, TransferLimitSerializer, TransferLogSerializer,
    TransferDashboardSerializer, AdminTransferSerializer
)
from .services import TransferService, AdminTransferService, TransferValidationError

logger = logging.getLogger(__name__)


class TransferViewSet(viewsets.ModelViewSet):
    """API endpoint for client transfer operations"""

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Get transfers for the authenticated user's account"""
        user = self.request.user

        # FIX: Get account number directly from user (Account object)
        account_number = user.account_number if hasattr(user, 'account_number') else None

        if not account_number:
            return Transfer.objects.none()

        # Get the Account object using the account_number
        from accounts.models import Account
        try:
            account = Account.objects.get(account_number=account_number)
            return Transfer.objects.filter(
                account=account
            ).select_related('tac').prefetch_related('logs').order_by('-created_at')
        except Account.DoesNotExist:
            return Transfer.objects.none()

    def get_serializer_class(self):
        if self.action == 'create':
            return TransferCreateSerializer
        elif self.action == 'retrieve':
            return TransferDetailSerializer
        return TransferSerializer

    def perform_create(self, serializer):
        """Create a new transfer with validation"""
        user = self.request.user  # user IS an Account instance

        # FIX: Get account number directly from user (Account object)
        account_number = user.account_number if hasattr(user, 'account_number') else None

        if not account_number:
            raise serializers.ValidationError("User account not found")

        # Get validated data
        data = serializer.validated_data

        # Validate transfer
        validation_errors = TransferService.validate_transfer(
            account_number=account_number,
            amount=data['amount']
        )

        if validation_errors:
            raise serializers.ValidationError(validation_errors)

        # Create transfer
        transfer = TransferService.create_transfer(
            account_number=account_number,
            amount=data['amount'],
            recipient_name=data['recipient_name'],
            destination_type=data['destination_type'],
            destination_details=data['destination_details'],
            narration=data.get('narration', '')
        )

        # Set the transfer instance for serializer
        serializer.instance = transfer
        return transfer  # ✅ FIXED: Return the created transfer

    def create(self, request, *args, **kwargs):
        """Override create to ensure proper response with full transfer data"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Call perform_create which now returns the transfer
            transfer = self.perform_create(serializer)
            
            # Get the proper serializer for response
            response_serializer = TransferSerializer(transfer, context={'request': request})
            
            # ✅ FIXED: Return the full transfer data with id, reference, etc.
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except serializers.ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating transfer: {str(e)}")
            return Response(
                {'error': 'Failed to create transfer'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def verify_tac(self, request, pk=None):
        """Verify TAC for a transfer"""
        transfer = self.get_object()

        # Check if transfer is in correct state
        if transfer.status != 'tac_sent':
            return Response(
                {'error': 'Transfer is not awaiting TAC verification'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = TACVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = TransferService.verify_tac(
                transfer_id=transfer.id,
                tac_code=serializer.validated_data['tac_code']
            )

            return Response(result, status=status.HTTP_200_OK)

        except TransferValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error verifying TAC: {str(e)}")
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get transfer summary for user"""
        user = request.user

        # FIX: Get account number directly from user (Account object)
        account_number = user.account_number if hasattr(user, 'account_number') else None

        if not account_number:
            return Response(
                {'error': 'Account not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        summary = TransferService.get_transfer_summary(account_number)
        return Response(summary, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending transfers for user"""
        user = request.user

        # FIX: Get account number directly from user (Account object)
        account_number = user.account_number if hasattr(user, 'account_number') else None

        if not account_number:
            return Response(
                {'error': 'Account not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get the Account object using the account_number
        from accounts.models import Account
        try:
            account = Account.objects.get(account_number=account_number)
            pending_transfers = Transfer.objects.filter(
                account=account,
                status__in=['pending', 'tac_sent', 'tac_verified']
            ).order_by('-created_at')
        except Account.DoesNotExist:
            pending_transfers = Transfer.objects.none()

        serializer = TransferSerializer(pending_transfers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get transfer history for user"""
        user = request.user

        # FIX: Get account number directly from user (Account object)
        account_number = user.account_number if hasattr(user, 'account_number') else None

        if not account_number:
            return Response(
                {'error': 'Account not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        transfers = TransferService.get_transfer_history(account_number)
        serializer = TransferSerializer(transfers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminTransferViewSet(viewsets.ModelViewSet):
    """API endpoint for admin transfer operations"""

    permission_classes = [permissions.IsAdminUser]
    queryset = Transfer.objects.all().select_related('account', 'tac').prefetch_related('logs')
    serializer_class = AdminTransferSerializer

    @action(detail=False, methods=['get'])
    def pending_tac(self, request):
        """Get transfers pending TAC generation"""
        pending_transfers = AdminTransferService.get_all_pending_transfers()
        serializer = self.get_serializer(pending_transfers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def pending_settlement(self, request):
        """Get transfers pending manual settlement"""
        pending_settlements = TransferService.get_pending_settlements()
        serializer = self.get_serializer(pending_settlements, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def generate_tac(self, request, pk=None):
        """Generate TAC for a transfer (admin only)"""
        transfer = self.get_object()

        if transfer.status != 'pending':
            return Response(
                {'error': 'Transfer is not pending TAC generation'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            tac_info = TransferService.generate_tac(transfer.id)

            # Log admin action
            TransferLog.objects.create(
                transfer=transfer,
                log_type='tac_sent',
                message=f'TAC generated by admin {request.user.email}',
                metadata={'admin_email': request.user.email}
            )

            return Response(tac_info, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error generating TAC: {str(e)}")
            return Response(
                {'error': 'Failed to generate TAC'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def settle(self, request, pk=None):
        """Mark transfer as settled (admin only)"""
        transfer = self.get_object()

        if transfer.status != 'funds_deducted':
            return Response(
                {'error': 'Transfer funds not deducted yet'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = TransferSettlementSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            transfer = TransferService.mark_as_settled(
                transfer_id=transfer.id,
                external_reference=serializer.validated_data['external_reference'],
                admin_notes=serializer.validated_data.get('admin_notes', '')
            )

            # Log admin action
            TransferLog.objects.create(
                transfer=transfer,
                log_type='settlement_completed',
                message=f'Transfer settled by admin {request.user.email}',
                metadata={
                    'admin_email': request.user.email,
                    'external_reference': serializer.validated_data['external_reference']
                }
            )

            serializer = self.get_serializer(transfer)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error settling transfer: {str(e)}")
            return Response(
                {'error': 'Failed to settle transfer'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a transfer (admin only)"""
        transfer = self.get_object()

        serializer = TransferCancelSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            transfer = AdminTransferService.cancel_transfer(
                transfer_id=transfer.id,
                reason=serializer.validated_data['reason']
            )

            serializer = self.get_serializer(transfer)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except TransferValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error cancelling transfer: {str(e)}")
            return Response(
                {'error': 'Failed to cancel transfer'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Get admin dashboard statistics"""
        stats = AdminTransferService.get_dashboard_stats()
        return Response(stats, status=status.HTTP_200_OK)


class TransferLimitViewSet(viewsets.ModelViewSet):
    """API endpoint for transfer limits (admin only)"""

    permission_classes = [permissions.IsAdminUser]
    queryset = TransferLimit.objects.all()
    serializer_class = TransferLimitSerializer


class TransferLogViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for viewing transfer logs (admin only)"""

    permission_classes = [permissions.IsAdminUser]
    serializer_class = TransferLogSerializer

    def get_queryset(self):
        transfer_id = self.request.query_params.get('transfer_id')

        if transfer_id:
            return TransferLog.objects.filter(transfer_id=transfer_id).order_by('-created_at')

        return TransferLog.objects.all().order_by('-created_at')[:100]