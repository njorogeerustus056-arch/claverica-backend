from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta
import random
from decimal import Decimal
from django.contrib.auth import get_user_model  # ← ADD THIS

from .models import Recipient, Transfer, TransferLog, TACCode
from .serializers import (
    RecipientSerializer, RecipientCreateSerializer,
    TransferSerializer, TransferCreateSerializer,
    TACCodeSerializer, TACVerifySerializer
)

User = get_user_model()  # ← ADD THIS


class RecipientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing transfer recipients
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Recipient.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return RecipientCreateSerializer
        return RecipientSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def toggle_favorite(self, request, pk=None):
        """Toggle favorite status of a recipient"""
        recipient = self.get_object()
        recipient.is_favorite = not recipient.is_favorite
        recipient.save()
        return Response({
            'status': 'success',
            'is_favorite': recipient.is_favorite
        })
    
    @action(detail=False, methods=['get'])
    def favorites(self, request):
        """Get all favorite recipients"""
        favorites = self.get_queryset().filter(is_favorite=True)
        serializer = self.get_serializer(favorites, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get recipients filtered by type"""
        recipient_type = request.query_params.get('type', None)
        if recipient_type:
            recipients = self.get_queryset().filter(recipient_type=recipient_type)
        else:
            recipients = self.get_queryset()
        
        serializer = self.get_serializer(recipients, many=True)
        return Response(serializer.data)


class TransferViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing transfers
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Transfer.objects.filter(sender=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TransferCreateSerializer
        return TransferSerializer
    
    def perform_create(self, serializer):
        # Calculate fee based on transfer type and amount
        transfer_type = serializer.validated_data.get('transfer_type')
        amount = serializer.validated_data.get('amount')
        
        # Fee calculation logic - using Decimal properly
        if transfer_type == 'crypto':
            fee = amount * Decimal('0.02')  # 2% for crypto
        elif transfer_type == 'international':
            fee = amount * Decimal('0.03')  # 3% for international
        else:
            fee = amount * Decimal('0.01')  # 1% for others
        
        # Minimum fee of $5
        if fee < Decimal('5.00'):
            fee = Decimal('5.00')
        
        # Determine if TAC is required (for amounts over $1000)
        requires_tac = amount >= Decimal('1000.00')
        
        transfer = serializer.save(
            sender=self.request.user,
            fee=fee,
            requires_tac=requires_tac
        )
        
        # Create log entry
        TransferLog.objects.create(
            transfer=transfer,
            status='pending',
            message='Transfer initiated',
            created_by=self.request.user
        )
        
        # Generate TAC if required
        if requires_tac:
            self._generate_tac(transfer)
    
    def _generate_tac(self, transfer):
        """Generate a 6-digit TAC code"""
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        expires_at = timezone.now() + timedelta(minutes=10)
        
        TACCode.objects.create(
            user=transfer.sender,
            transfer=transfer,
            code=code,
            expires_at=expires_at
        )
        
        # TODO: Send TAC code via email/SMS
        # For now, just log it
        print(f"TAC Code generated for transfer {transfer.transfer_id}: {code}")
    
    @action(detail=True, methods=['post'])
    def verify_tac(self, request, pk=None):
        """Verify TAC code for a transfer"""
        transfer = self.get_object()
        serializer = TACVerifySerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        tac_code = serializer.validated_data['tac_code']
        
        # Find valid TAC code
        tac = TACCode.objects.filter(
            user=request.user,
            transfer=transfer,
            code=tac_code,
            is_used=False
        ).first()
        
        if not tac:
            return Response({
                'status': 'error',
                'message': 'Invalid TAC code'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not tac.is_valid():
            return Response({
                'status': 'error',
                'message': 'TAC code has expired'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Mark TAC as used
        tac.is_used = True
        tac.used_at = timezone.now()
        tac.save()
        
        # Update transfer
        transfer.tac_verified = True
        transfer.tac_verified_at = timezone.now()
        transfer.status = 'processing'
        transfer.save()
        
        # Create log entry
        TransferLog.objects.create(
            transfer=transfer,
            status='processing',
            message='TAC verified, transfer processing',
            created_by=request.user
        )
        
        return Response({
            'status': 'success',
            'message': 'TAC verified successfully',
            'transfer': TransferSerializer(transfer).data
        })
    
    @action(detail=True, methods=['post'])
    def resend_tac(self, request, pk=None):
        """Resend TAC code"""
        transfer = self.get_object()
        
        if not transfer.requires_tac:
            return Response({
                'status': 'error',
                'message': 'This transfer does not require TAC'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Invalidate old TAC codes
        TACCode.objects.filter(
            user=request.user,
            transfer=transfer,
            is_used=False
        ).update(is_used=True)
        
        # Generate new TAC
        self._generate_tac(transfer)
        
        return Response({
            'status': 'success',
            'message': 'New TAC code has been sent'
        })
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a pending transfer"""
        transfer = self.get_object()
        
        if transfer.status not in ['pending', 'processing']:
            return Response({
                'status': 'error',
                'message': 'Only pending or processing transfers can be cancelled'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        transfer.status = 'cancelled'
        transfer.save()
        
        # Create log entry
        TransferLog.objects.create(
            transfer=transfer,
            status='cancelled',
            message='Transfer cancelled by user',
            created_by=request.user
        )
        
        return Response({
            'status': 'success',
            'message': 'Transfer cancelled successfully'
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get transfer statistics"""
        queryset = self.get_queryset()
        
        total_transfers = queryset.count()
        pending = queryset.filter(status='pending').count()
        processing = queryset.filter(status='processing').count()
        completed = queryset.filter(status='completed').count()
        failed = queryset.filter(status='failed').count()
        
        total_sent = queryset.filter(status='completed').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        return Response({
            'total_transfers': total_transfers,
            'pending': pending,
            'processing': processing,
            'completed': completed,
            'failed': failed,
            'total_sent': float(total_sent),
            'currency': 'USD'
        })
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent transfers"""
        limit = int(request.query_params.get('limit', 10))
        transfers = self.get_queryset()[:limit]
        serializer = self.get_serializer(transfers, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_status(self, request):
        """Get transfers filtered by status"""
        transfer_status = request.query_params.get('status', None)
        if transfer_status:
            transfers = self.get_queryset().filter(status=transfer_status)
        else:
            transfers = self.get_queryset()
        
        serializer = self.get_serializer(transfers, many=True)
        return Response(serializer.data)