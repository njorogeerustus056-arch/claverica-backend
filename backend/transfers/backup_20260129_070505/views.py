"""
transfers/views.py - Updated with compliance integration
"""

import logging
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, Count, Q
from django.shortcuts import get_object_or_404

from .models import Transfer, TransferLog, TransferLimit
from .serializers import (
    TransferCreateSerializer, TransferSerializer, TransferUpdateSerializer,
    TransferLogSerializer, TransferLimitSerializer, TACVerificationSerializer,
    TransferStatusUpdateSerializer, TransferDashboardSerializer
)
from .services import TransferComplianceService

logger = logging.getLogger(__name__)


class TransferViewSet(viewsets.ModelViewSet):
    """API endpoint for transfers with compliance integration"""
    
    queryset = Transfer.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TransferCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TransferUpdateSerializer
        return TransferSerializer
    
    def get_queryset(self):
        """Filter transfers based on user role"""
        user = self.request.user
        
        if user.is_staff or user.groups.filter(name__in=['Compliance Officers', 'Finance Managers']).exists():
            queryset = Transfer.objects.all()
        else:
            queryset = Transfer.objects.filter(user=user)
        
        # Apply filters
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        
        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        amount_min = self.request.query_params.get('amount_min')
        if amount_min:
            queryset = queryset.filter(amount__gte=amount_min)
        
        amount_max = self.request.query_params.get('amount_max')
        if amount_max:
            queryset = queryset.filter(amount__lte=amount_max)
        
        recipient = self.request.query_params.get('recipient')
        if recipient:
            queryset = queryset.filter(
                Q(recipient_name__icontains=recipient) |
                Q(recipient_account__icontains=recipient) |
                Q(recipient_email__icontains=recipient)
            )
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Create transfer with compliance check"""
        return serializer.save()
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit transfer for processing"""
        transfer = self.get_object()
        
        if transfer.user != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if transfer.status != 'draft':
            return Response(
                {'error': f'Transfer is already {transfer.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Check KYC status
            if not transfer.check_kyc_status():
                return Response(
                    {'error': 'KYC verification required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update status
            transfer.status = 'pending'
            transfer.submitted_at = timezone.now()
            transfer.save()
            
            # Perform compliance assessment
            risk_assessment = TransferComplianceService.assess_transfer_risk(transfer)
            
            # Create audit log
            TransferLog.objects.create(
                transfer=transfer,
                log_type='status_change',
                message='Transfer submitted for processing',
                created_by=request.user,
                metadata={'new_status': 'pending', 'risk_assessment': risk_assessment}
            )
            
            return Response({
                'success': True,
                'message': 'Transfer submitted successfully',
                'transfer_id': transfer.transfer_id,
                'status': transfer.status,
                'risk_level': transfer.risk_level,
                'tac_required': transfer.tac_required,
                'video_call_required': transfer.video_call_required,
                'next_steps': 'Awaiting compliance checks' if transfer.risk_level != 'low' else 'Ready for processing'
            })
        
        except Exception as e:
            logger.error(f"Transfer submission error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def generate_tac(self, request, pk=None):
        """Generate TAC for transfer"""
        transfer = self.get_object()
        
        if not transfer.tac_required:
            return Response(
                {'error': 'TAC not required for this transfer'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = TransferComplianceService.generate_tac_for_transfer(transfer)
            
            if result['success']:
                return Response({
                    'success': True,
                    'message': 'TAC generated successfully',
                    'transfer_id': transfer.transfer_id,
                    'status': transfer.status,
                    'note': 'TAC will be sent to the registered contact methods'
                })
            else:
                return Response(
                    {'error': result.get('error', 'TAC generation failed')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            logger.error(f"TAC generation error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def verify_tac(self, request):
        """Verify TAC for transfer"""
        serializer = TACVerificationSerializer(data=request.data, context={'request': request})
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        transfer = serializer.validated_data['transfer']
        tac_code = serializer.validated_data['tac_code']
        
        try:
            result = TransferComplianceService.verify_tac_for_transfer(transfer, tac_code)
            
            if result['success']:
                return Response({
                    'success': True,
                    'message': 'TAC verified successfully',
                    'transfer_id': transfer.transfer_id,
                    'status': transfer.status,
                    'next_steps': 'Video call verification required' if transfer.video_call_required else 'Awaiting processing'
                })
            else:
                return Response(
                    {'error': result.get('error', 'TAC verification failed')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            logger.error(f"TAC verification error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def schedule_video_call(self, request, pk=None):
        """Schedule video call for transfer verification"""
        transfer = self.get_object()
        
        if not transfer.video_call_required:
            return Response(
                {'error': 'Video call not required for this transfer'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        scheduled_for = request.data.get('scheduled_for')
        
        try:
            result = TransferComplianceService.schedule_video_call(transfer, scheduled_for)
            
            if result['success']:
                return Response({
                    'success': True,
                    'message': 'Video call scheduled successfully',
                    'transfer_id': transfer.transfer_id,
                    'session_id': result.get('session_id'),
                    'scheduled_for': result.get('scheduled_for'),
                    'status': transfer.status
                })
            else:
                return Response(
                    {'error': result.get('error', 'Failed to schedule video call')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            logger.error(f"Video call scheduling error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """Process transfer"""
        transfer = self.get_object()
        
        # Check permissions
        if not request.user.is_staff and transfer.user != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            result = TransferComplianceService.process_transfer(transfer)
            
            if result['success']:
                return Response({
                    'success': True,
                    'message': 'Transfer processing started',
                    'transfer_id': transfer.transfer_id,
                    'status': transfer.status
                })
            else:
                return Response(
                    {'error': result.get('error', 'Transfer processing failed')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            logger.error(f"Transfer processing error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark transfer as completed"""
        transfer = self.get_object()
        
        if transfer.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if transfer.status != 'processing':
            return Response(
                {'error': f'Transfer is not processing (current status: {transfer.status})'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            transfer.status = 'completed'
            transfer.completed_at = timezone.now()
            transfer.save()
            
            # Update compliance request if exists
            if transfer.compliance_request:
                transfer.compliance_request.status = 'completed'
                transfer.compliance_request.save()
            
            # Create audit log
            TransferLog.objects.create(
                transfer=transfer,
                log_type='completed',
                message='Transfer completed successfully',
                created_by=request.user
            )
            
            return Response({
                'success': True,
                'message': 'Transfer marked as completed',
                'transfer_id': transfer.transfer_id,
                'status': transfer.status,
                'completed_at': transfer.completed_at
            })
        
        except Exception as e:
            logger.error(f"Transfer completion error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel transfer"""
        transfer = self.get_object()
        reason = request.data.get('reason', '')
        
        if transfer.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if transfer can be cancelled
        if transfer.status in ['completed', 'failed', 'cancelled']:
            return Response(
                {'error': f'Cannot cancel transfer with status: {transfer.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            old_status = transfer.status
            transfer.status = 'cancelled'
            transfer.save()
            
            # Update compliance request if exists
            if transfer.compliance_request:
                transfer.compliance_request.status = 'cancelled'
                transfer.compliance_request.save()
            
            # Create audit log
            TransferLog.objects.create(
                transfer=transfer,
                log_type='cancelled',
                message=f'Transfer cancelled: {reason}',
                created_by=request.user,
                metadata={'old_status': old_status, 'reason': reason}
            )
            
            return Response({
                'success': True,
                'message': 'Transfer cancelled successfully',
                'transfer_id': transfer.transfer_id,
                'status': transfer.status
            })
        
        except Exception as e:
            logger.error(f"Transfer cancellation error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def compliance_status(self, request, pk=None):
        """Get compliance status for transfer"""
        transfer = self.get_object()
        
        try:
            result = TransferComplianceService.check_compliance_status(transfer)
            
            return Response({
                'success': True,
                'transfer_id': transfer.transfer_id,
                'transfer_status': transfer.status,
                'compliance_status': result['status'],
                'message': result['message'],
                'risk_level': transfer.risk_level,
                'tac_required': transfer.tac_required,
                'video_call_required': transfer.video_call_required,
                'kyc_status': transfer.check_kyc_status()
            })
        
        except Exception as e:
            logger.error(f"Compliance status check error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Get logs for transfer"""
        transfer = self.get_object()
        
        if transfer.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        logs = transfer.logs.all().order_by('-created_at')
        return Response({
            'success': True,
            'transfer_id': transfer.transfer_id,
            'logs': TransferLogSerializer(logs, many=True).data,
            'count': logs.count()
        })
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get transfer dashboard statistics"""
        user = request.user
        
        try:
            # Get base queryset
            if user.is_staff:
                queryset = Transfer.objects.all()
            else:
                queryset = Transfer.objects.filter(user=user)
            
            # Calculate statistics
            total_transfers = queryset.count()
            total_amount = queryset.aggregate(total=Sum('amount'))['total'] or 0
            
            pending_transfers = queryset.filter(status__in=['pending', 'awaiting_tac', 'awaiting_video_call', 'compliance_review']).count()
            completed_transfers = queryset.filter(status='completed').count()
            failed_transfers = queryset.filter(status='failed').count()
            
            average_amount = total_amount / total_transfers if total_transfers > 0 else 0
            
            # Get recent transfers
            recent_transfers = queryset.order_by('-created_at')[:10]
            
            # Get compliance-related stats (for staff only)
            compliance_stats = {}
            if user.is_staff:
                compliance_stats = {
                    'high_risk_transfers': queryset.filter(risk_level='high').count(),
                    'tac_required': queryset.filter(tac_required=True).count(),
                    'video_call_required': queryset.filter(video_call_required=True).count(),
                    'pending_compliance': queryset.filter(status='compliance_review').count(),
                }
            
            return Response({
                'success': True,
                'statistics': {
                    'total_transfers': total_transfers,
                    'total_amount': float(total_amount),
                    'pending_transfers': pending_transfers,
                    'completed_transfers': completed_transfers,
                    'failed_transfers': failed_transfers,
                    'average_transfer_amount': float(average_amount),
                },
                'compliance_stats': compliance_stats,
                'recent_transfers': TransferSerializer(recent_transfers, many=True).data
            })
        
        except Exception as e:
            logger.error(f"Dashboard error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TransferLimitViewSet(viewsets.ModelViewSet):
    """API endpoint for transfer limits"""
    
    queryset = TransferLimit.objects.all()
    serializer_class = TransferLimitSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter limits based on user role"""
        user = self.request.user
        
        if user.is_staff:
            queryset = TransferLimit.objects.all()
        else:
            # Users can only see their own limits or global limits
            queryset = TransferLimit.objects.filter(
                Q(user=user) | Q(user__isnull=True)
            )
        
        limit_type = self.request.query_params.get('limit_type')
        if limit_type:
            queryset = queryset.filter(limit_type=limit_type)
        
        currency = self.request.query_params.get('currency')
        if currency:
            queryset = queryset.filter(currency=currency)
        
        return queryset.order_by('limit_type', 'country')
    
    def perform_create(self, serializer):
        """Only staff can create transfer limits"""
        if not self.request.user.is_staff:
            raise PermissionError("Only staff can create transfer limits")
        return serializer.save()


class TransferSearchView(APIView):
    """API endpoint for searching transfers"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Search transfers"""
        query = request.query_params.get('q', '')
        
        if not query:
            return Response(
                {'error': 'Search query is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        
        try:
            if user.is_staff:
                transfers = Transfer.objects.filter(
                    Q(transfer_id__icontains=query) |
                    Q(user__email__icontains=query) |
                    Q(recipient_name__icontains=query) |
                    Q(recipient_account__icontains=query) |
                    Q(recipient_email__icontains=query) |
                    Q(reference__icontains=query)
                )[:20]
            else:
                transfers = Transfer.objects.filter(user=user).filter(
                    Q(transfer_id__icontains=query) |
                    Q(recipient_name__icontains=query) |
                    Q(recipient_account__icontains=query) |
                    Q(recipient_email__icontains=query) |
                    Q(reference__icontains=query)
                )[:20]
            
            return Response({
                'success': True,
                'query': query,
                'results': TransferSerializer(transfers, many=True).data,
                'count': transfers.count()
            })
        
        except Exception as e:
            logger.error(f"Transfer search error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )