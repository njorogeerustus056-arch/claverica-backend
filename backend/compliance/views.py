"""
compliance/views.py - Django REST Framework views for central compliance app
"""

import logging
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import api_view, parser_classes, permission_classes, action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.conf import settings

from .models import (
    ComplianceRequest, KYCVerification, KYCDocument,
    TACRequest, VideoCallSession, ComplianceAuditLog,
    ComplianceRule, ComplianceDashboardStats, ComplianceAlert, ComplianceProfile
)
from .serializers import (
    ComplianceRequestSerializer, ComplianceRequestCreateSerializer,
    KYCVerificationSerializer, KYCDocumentSerializer, KYCDocumentUploadSerializer,
    TACRequestSerializer, TACGenerateSerializer, TACVerifySerializer,
    VideoCallSessionSerializer, VideoCallScheduleSerializer,
    ComplianceAuditLogSerializer, ComplianceRuleSerializer,
    ComplianceDashboardStatsSerializer, ComplianceAlertSerializer,
    ComplianceAlertCreateSerializer, ComplianceDashboardSummarySerializer,
    ComplianceSearchSerializer, ComplianceBulkActionSerializer,
    UserSerializer
)
from .services import (
    ComplianceService, KYCService, TACService,
    VideoCallService, AuditService, AlertService
)
from .permissions import (
    IsComplianceOfficer, IsOwnerOrAdmin, HasKYCApproved,
    CanViewAuditLogs, CanManageDocuments, CanApproveKYC
)
from .email_service import (
    send_compliance_decision_email,
    send_compliance_escalation_email
)

logger = logging.getLogger(__name__)
User = get_user_model()


class ComplianceRequestViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing compliance requests
    """
    queryset = ComplianceRequest.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ComplianceRequestCreateSerializer
        return ComplianceRequestSerializer
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        elif self.action == 'create':
            permission_classes = [IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsComplianceOfficer]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Users can see their own requests
        Compliance officers can see all requests
        """
        user = self.request.user
        
        if user.is_staff or user.groups.filter(name='Compliance Officers').exists():
            queryset = ComplianceRequest.objects.all()
        else:
            queryset = ComplianceRequest.objects.filter(user=user)
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        app_filter = self.request.query_params.get('app')
        if app_filter:
            queryset = queryset.filter(app_name=app_filter)
        
        type_filter = self.request.query_params.get('type')
        if type_filter:
            queryset = queryset.filter(request_type=type_filter)
        
        priority_filter = self.request.query_params.get('priority')
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)
        
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        
        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get dashboard statistics for compliance requests"""
        user = request.user
        
        try:
            total_requests = self.get_queryset().count()
            pending_requests = self.get_queryset().filter(status='pending').count()
            high_priority = self.get_queryset().filter(priority='high').count()
            
            recent_requests = self.get_queryset()[:10]
            
            return Response({
                'success': True,
                'statistics': {
                    'total_requests': total_requests,
                    'pending_requests': pending_requests,
                    'high_priority_requests': high_priority,
                    'in_review': self.get_queryset().filter(status='under_review').count(),
                    'awaiting_tac': self.get_queryset().filter(status='awaiting_tac').count(),
                },
                'recent_requests': ComplianceRequestSerializer(recent_requests, many=True).data
            })
        
        except Exception as e:
            logger.error(f"Dashboard error: {str(e)}")
            return Response(
                {'error': 'Failed to load dashboard'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a compliance request"""
        if not request.user.is_staff and not request.user.groups.filter(name='Compliance Officers').exists():
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        compliance_request = self.get_object()
        notes = request.data.get('notes', '')
        
        try:
            result = ComplianceService.approve_request(
                compliance_request=compliance_request,
                approved_by=request.user,
                notes=notes
            )
            
            if result['success']:
                try:
                    user = compliance_request.user
                    user_name = f"{user.first_name} {user.last_name}" if user.first_name else user.email
                    send_compliance_decision_email(
                        user.email,
                        user_name,
                        "Compliance Request Approved",
                        "approved",
                        f"Your compliance request {compliance_request.compliance_id} has been approved."
                    )
                except Exception as e:
                    logger.error(f"Failed to send approval email: {e}")
            
            if result['success']:
                return Response(result)
            else:
                return Response(
                    {'error': result.get('error', 'Approval failed')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            logger.error(f"Approval error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a compliance request"""
        if not request.user.is_staff and not request.user.groups.filter(name='Compliance Officers').exists():
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        compliance_request = self.get_object()
        reason = request.data.get('reason', '')
        notes = request.data.get('notes', '')
        
        if not reason:
            return Response(
                {'error': 'Rejection reason is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = ComplianceService.reject_request(
                compliance_request=compliance_request,
                rejected_by=request.user,
                reason=reason,
                notes=notes
            )
            
            if result['success']:
                try:
                    user = compliance_request.user
                    user_name = f"{user.first_name} {user.last_name}" if user.first_name else user.email
                    send_compliance_decision_email(
                        user.email,
                        user_name,
                        "Compliance Request Rejected",
                        "rejected",
                        f"Your compliance request {compliance_request.compliance_id} has been rejected. Reason: {reason}"
                    )
                except Exception as e:
                    logger.error(f"Failed to send rejection email: {e}")
            
            if result['success']:
                return Response(result)
            else:
                return Response(
                    {'error': result.get('error', 'Rejection failed')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            logger.error(f"Rejection error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def escalate(self, request, pk=None):
        """Escalate a compliance request"""
        compliance_request = self.get_object()
        reason = request.data.get('reason', '')
        
        try:
            result = ComplianceService.escalate_request(
                compliance_request=compliance_request,
                escalated_by=request.user,
                reason=reason
            )
            
            if result['success']:
                try:
                    user = compliance_request.user
                    user_name = f"{user.first_name} {user.last_name}" if user.first_name else user.email
                    escalated_to = compliance_request.escalated_to.email if compliance_request.escalated_to else "Senior Compliance Officer"
                    send_compliance_escalation_email(
                        user.email,
                        user_name,
                        compliance_request.compliance_id,
                        escalated_to,
                        reason or ""
                    )
                except Exception as e:
                    logger.error(f"Failed to send escalation email: {e}")
            
            if result['success']:
                return Response(result)
            else:
                return Response(
                    {'error': result.get('error', 'Escalation failed')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            logger.error(f"Escalation error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign a compliance request to an officer"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        compliance_request = self.get_object()
        officer_id = request.data.get('officer_id')
        
        if not officer_id:
            return Response(
                {'error': 'officer_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            officer = User.objects.get(id=officer_id)
            
            if not officer.is_staff and not officer.groups.filter(name='Compliance Officers').exists():
                return Response(
                    {'error': 'User is not a compliance officer'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            compliance_request.assigned_to = officer
            compliance_request.save()
            
            AuditService.log_action(
                user=request.user,
                action=f"Assigned compliance request {compliance_request.compliance_id} to {officer.email}",
                entity_type='compliance_request',
                entity_id=compliance_request.compliance_id,
                old_value={'assigned_to': None},
                new_value={'assigned_to': officer.email}
            )
            
            return Response({
                'success': True,
                'message': f'Request assigned to {officer.email}',
                'assigned_to': officer.email
            })
        
        except User.DoesNotExist:
            return Response(
                {'error': 'Officer not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Assignment error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def request_info(self, request, pk=None):
        """Request additional information for a compliance request"""
        if not request.user.is_staff and not request.user.groups.filter(name='Compliance Officers').exists():
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        compliance_request = self.get_object()
        info_required = request.data.get('info_required', '')
        
        if not info_required:
            return Response(
                {'error': 'info_required is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = ComplianceService.request_additional_info(
                compliance_request=compliance_request,
                requested_by=request.user,
                info_required=info_required
            )
            
            if result['success']:
                return Response(result)
            else:
                return Response(
                    {'error': result.get('error', 'Request failed')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            logger.error(f"Info request error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """Perform bulk actions on compliance requests"""
        if not request.user.is_staff and not request.user.groups.filter(name='Compliance Officers').exists():
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ComplianceBulkActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        action_type = data['action']
        item_ids = data['item_ids']
        
        try:
            requests = ComplianceRequest.objects.filter(compliance_id__in=item_ids)
            
            if action_type == 'approve':
                for req in requests:
                    ComplianceService.approve_request(
                        compliance_request=req,
                        approved_by=request.user,
                        notes=data.get('notes', '')
                    )
            
            elif action_type == 'reject':
                for req in requests:
                    ComplianceService.reject_request(
                        compliance_request=req,
                        rejected_by=request.user,
                        reason=data.get('notes', 'Bulk rejection'),
                        notes=data.get('notes', '')
                    )
            
            elif action_type == 'assign':
                officer = User.objects.get(id=data['assigned_to'])
                for req in requests:
                    req.assigned_to = officer
                    req.save()
            
            return Response({
                'success': True,
                'message': f'Performed {action_type} on {len(requests)} requests',
                'processed': len(requests)
            })
        
        except Exception as e:
            logger.error(f"Bulk action error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search compliance requests"""
        query = request.query_params.get('q', '')
        
        if not query:
            return Response(
                {'error': 'Search query is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            requests = ComplianceRequest.objects.filter(
                Q(compliance_id__icontains=query) |
                Q(user__email__icontains=query) |
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) |
                Q(description__icontains=query)
            )[:20]
            
            return Response({
                'success': True,
                'results': ComplianceRequestSerializer(requests, many=True).data,
                'count': requests.count()
            })
        
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class KYCVerificationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for KYC verifications
    """
    queryset = KYCVerification.objects.all()
    serializer_class = KYCVerificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        elif self.action in ['create', 'update', 'partial_update']:
            permission_classes = [IsAuthenticated]
        elif self.action in ['destroy', 'approve', 'reject']:
            permission_classes = [IsComplianceOfficer]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter queryset based on user role"""
        user = self.request.user
        
        if user.is_staff or user.groups.filter(name='Compliance Officers').exists():
            queryset = KYCVerification.objects.all()
        else:
            queryset = KYCVerification.objects.filter(user=user)
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(verification_status=status_filter)
        
        risk_filter = self.request.query_params.get('risk_level')
        if risk_filter:
            queryset = queryset.filter(risk_level=risk_filter)
        
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        
        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Create KYC verification with additional processing"""
        kyc_verification = serializer.save()
        
        KYCService.perform_initial_checks(kyc_verification)
        
        AuditService.log_action(
            user=self.request.user,
            action='KYC Verification Created',
            entity_type='kyc_verification',
            entity_id=kyc_verification.kyc_id,
            new_value={'status': kyc_verification.verification_status}
        )
    
    @action(detail=True, methods=['post'])
    def submit_document(self, request, pk=None):
        """Submit document for KYC verification"""
        kyc_verification = self.get_object()
        
        if kyc_verification.user != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = KYCDocumentUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            result = KYCService.upload_document(
                kyc_verification=kyc_verification,
                user=request.user,
                document_data=serializer.validated_data,
                file=serializer.validated_data['file']
            )
            
            if result['success']:
                return Response(result, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'error': result.get('error', 'Document upload failed')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            logger.error(f"Document upload error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve KYC verification"""
        if not request.user.is_staff and not request.user.groups.filter(name='Compliance Officers').exists():
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        kyc_verification = self.get_object()
        notes = request.data.get('notes', '')
        compliance_level = request.data.get('compliance_level', 'standard')
        
        try:
            result = KYCService.approve_verification(
                kyc_verification=kyc_verification,
                approved_by=request.user,
                notes=notes,
                compliance_level=compliance_level
            )
            
            if result['success']:
                return Response(result)
            else:
                return Response(
                    {'error': result.get('error', 'Approval failed')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            logger.error(f"KYC approval error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject KYC verification"""
        if not request.user.is_staff and not request.user.groups.filter(name='Compliance Officers').exists():
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        kyc_verification = self.get_object()
        reason = request.data.get('reason', '')
        
        if not reason:
            return Response(
                {'error': 'Rejection reason is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = KYCService.reject_verification(
                kyc_verification=kyc_verification,
                rejected_by=request.user,
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
            logger.error(f"KYC rejection error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """Get documents for KYC verification"""
        kyc_verification = self.get_object()
        
        if kyc_verification.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        documents = kyc_verification.documents.all()
        return Response({
            'success': True,
            'documents': KYCDocumentSerializer(documents, many=True).data,
            'count': documents.count()
        })
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """Get current user's KYC status"""
        try:
            kyc = KYCVerification.objects.filter(user=request.user).order_by('-created_at').first()
            
            if not kyc:
                return Response({
                    'success': True,
                    'has_kyc': False,
                    'message': 'No KYC verification found'
                })
            
            return Response({
                'success': True,
                'has_kyc': True,
                'kyc': KYCVerificationSerializer(kyc).data,
                'compliance_level': kyc.compliance_level,
                'is_approved': kyc.verification_status == 'approved'
            })
        
        except Exception as e:
            logger.error(f"KYC status error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class KYCDocumentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for KYC documents
    """
    queryset = KYCDocument.objects.all()
    serializer_class = KYCDocumentSerializer
    permission_classes = [IsAuthenticated, CanManageDocuments]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_queryset(self):
        """Filter documents based on user role"""
        user = self.request.user
        
        if user.is_staff or user.groups.filter(name='Compliance Officers').exists():
            queryset = KYCDocument.objects.all()
        else:
            queryset = KYCDocument.objects.filter(user=user)
        
        type_filter = self.request.query_params.get('type')
        if type_filter:
            queryset = queryset.filter(document_type=type_filter)
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        kyc_id = self.request.query_params.get('kyc_id')
        if kyc_id:
            queryset = queryset.filter(kyc_verification__kyc_id=kyc_id)
        
        return queryset.order_by('-uploaded_at')
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify a document"""
        if not request.user.is_staff and not request.user.groups.filter(name='Compliance Officers').exists():
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        document = self.get_object()
        status_value = request.data.get('status')
        notes = request.data.get('notes', '')
        rejection_reason = request.data.get('rejection_reason', '')
        
        if status_value not in ['approved', 'rejected']:
            return Response(
                {'error': 'Status must be either approved or rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if status_value == 'rejected' and not rejection_reason:
            return Response(
                {'error': 'Rejection reason is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = KYCService.verify_document(
                document=document,
                verified_by=request.user,
                status=status_value,
                notes=notes,
                rejection_reason=rejection_reason
            )
            
            if result['success']:
                return Response(result)
            else:
                return Response(
                    {'error': result.get('error', 'Verification failed')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            logger.error(f"Document verification error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download a document"""
        document = self.get_object()
        
        if document.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return Response({
            'success': True,
            'file_name': document.original_file_name,
            'file_type': document.file_type,
            'file_size': document.file_size,
            'file_url': document.file_url,
            'download_url': f'/api/compliance/documents/{document.document_id}/download-file/'
        })


class TACRequestViewSet(viewsets.ModelViewSet):
    """
    API endpoint for TAC requests
    """
    queryset = TACRequest.objects.all()
    serializer_class = TACRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter TAC requests based on user role"""
        user = self.request.user
        
        if user.is_staff or user.groups.filter(name='Compliance Officers').exists():
            queryset = TACRequest.objects.all()
        else:
            queryset = TACRequest.objects.filter(user=user)
        
        is_valid = self.request.query_params.get('is_valid')
        if is_valid == 'true':
            queryset = queryset.filter(
                is_used=False,
                is_expired=False,
                expires_at__gt=timezone.now()
            )
        elif is_valid == 'false':
            queryset = queryset.filter(
                Q(is_used=True) | Q(is_expired=True) | Q(expires_at__lte=timezone.now())
            )
        
        tac_type = self.request.query_params.get('type')
        if tac_type:
            queryset = queryset.filter(tac_type=tac_type)
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate a new TAC"""
        serializer = TACGenerateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            result = TACService.generate_tac(
                user=request.user,
                **serializer.validated_data
            )
            
            if result['success']:
                return Response(result, status=status.HTTP_201_CREATED)
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
    def verify(self, request):
        """Verify a TAC"""
        serializer = TACVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            result = TACService.verify_tac(
                user=request.user,
                **serializer.validated_data
            )
            
            if result['success']:
                return Response(result)
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
    def resend(self, request, pk=None):
        """Resend a TAC"""
        tac_request = self.get_object()
        
        if tac_request.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not tac_request.is_valid():
            return Response(
                {'error': 'TAC is no longer valid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = TACService.resend_tac(tac_request)
            
            if result['success']:
                return Response(result)
            else:
                return Response(
                    {'error': result.get('error', 'TAC resend failed')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            logger.error(f"TAC resend error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VideoCallSessionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for video call sessions
    """
    queryset = VideoCallSession.objects.all()
    serializer_class = VideoCallSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter video calls based on user role"""
        user = self.request.user
        
        if user.is_staff or user.groups.filter(name='Compliance Officers').exists():
            queryset = VideoCallSession.objects.all()
        else:
            queryset = VideoCallSession.objects.filter(user=user)
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        upcoming = self.request.query_params.get('upcoming')
        if upcoming == 'true':
            queryset = queryset.filter(
                status__in=['scheduled', 'rescheduled'],
                scheduled_for__gt=timezone.now()
            )
        
        return queryset.order_by('scheduled_for')
    
    @action(detail=False, methods=['post'])
    def schedule(self, request):
        """Schedule a new video call"""
        serializer = VideoCallScheduleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            result = VideoCallService.schedule_call(
                requested_by=request.user,
                **serializer.validated_data
            )
            
            if result['success']:
                return Response(result, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'error': result.get('error', 'Scheduling failed')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            logger.error(f"Video call scheduling error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start a video call session"""
        video_call = self.get_object()
        
        if video_call.user != request.user and video_call.agent != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            result = VideoCallService.start_call(video_call)
            
            if result['success']:
                return Response(result)
            else:
                return Response(
                    {'error': result.get('error', 'Failed to start call')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            logger.error(f"Video call start error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete a video call session"""
        video_call = self.get_object()
        
        if video_call.agent != request.user:
            return Response(
                {'error': 'Only the assigned agent can complete the call'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        verification_passed = request.data.get('verification_passed', False)
        notes = request.data.get('notes', '')
        
        try:
            result = VideoCallService.complete_call(
                video_call=video_call,
                completed_by=request.user,
                verification_passed=verification_passed,
                notes=notes
            )
            
            if result['success']:
                return Response(result)
            else:
                return Response(
                    {'error': result.get('error', 'Failed to complete call')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            logger.error(f"Video call completion error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def reschedule(self, request, pk=None):
        """Reschedule a video call"""
        video_call = self.get_object()
        new_time = request.data.get('scheduled_for')
        
        if not new_time:
            return Response(
                {'error': 'scheduled_for is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = VideoCallService.reschedule_call(
                video_call=video_call,
                new_time=new_time,
                rescheduled_by=request.user
            )
            
            if result['success']:
                return Response(result)
            else:
                return Response(
                    {'error': result.get('error', 'Rescheduling failed')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            logger.error(f"Video call reschedule error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a video call"""
        video_call = self.get_object()
        reason = request.data.get('reason', '')
        
        if video_call.user != request.user and video_call.agent != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            result = VideoCallService.cancel_call(
                video_call=video_call,
                cancelled_by=request.user,
                reason=reason
            )
            
            if result['success']:
                return Response(result)
            else:
                return Response(
                    {'error': result.get('error', 'Cancellation failed')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            logger.error(f"Video call cancellation error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ComplianceAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for compliance audit logs (read-only)
    """
    queryset = ComplianceAuditLog.objects.all()
    serializer_class = ComplianceAuditLogSerializer
    permission_classes = [IsAuthenticated, CanViewAuditLogs]
    
    def get_queryset(self):
        """Filter audit logs based on user role"""
        user = self.request.user
        
        if user.is_staff or user.groups.filter(name='Compliance Officers').exists():
            queryset = ComplianceAuditLog.objects.all()
        else:
            queryset = ComplianceAuditLog.objects.filter(user=user)
        
        entity_type = self.request.query_params.get('entity_type')
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)
        
        entity_id = self.request.query_params.get('entity_id')
        if entity_id:
            queryset = queryset.filter(entity_id=entity_id)
        
        action_type = self.request.query_params.get('action_type')
        if action_type:
            queryset = queryset.filter(action_type=action_type)
        
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        
        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent audit logs"""
        limit = int(request.query_params.get('limit', 50))
        
        logs = self.get_queryset()[:limit]
        return Response({
            'success': True,
            'logs': self.get_serializer(logs, many=True).data,
            'count': logs.count()
        })


class ComplianceRuleViewSet(viewsets.ModelViewSet):
    """
    API endpoint for compliance rules
    """
    queryset = ComplianceRule.objects.all()
    serializer_class = ComplianceRuleSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        """Filter rules"""
        queryset = ComplianceRule.objects.all()
        
        is_active = self.request.query_params.get('is_active')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)
        
        rule_type = self.request.query_params.get('rule_type')
        if rule_type:
            queryset = queryset.filter(rule_type=rule_type)
        
        app = self.request.query_params.get('app')
        if app:
            queryset = queryset.filter(
                Q(applicable_apps='all') | Q(applicable_apps=app)
            )
        
        return queryset.order_by('priority', 'rule_name')
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a compliance rule"""
        rule = self.get_object()
        rule.is_active = True
        rule.save()
        
        return Response({
            'success': True,
            'message': 'Rule activated',
            'rule': self.get_serializer(rule).data
        })
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a compliance rule"""
        rule = self.get_object()
        rule.is_active = False
        rule.save()
        
        return Response({
            'success': True,
            'message': 'Rule deactivated',
            'rule': self.get_serializer(rule).data
        })
    
    @action(detail=False, methods=['get'])
    def evaluate(self, request):
        """Evaluate compliance rules against a transaction"""
        amount = request.query_params.get('amount')
        currency = request.query_params.get('currency', 'USD')
        user_id = request.query_params.get('user_id')
        app = request.query_params.get('app')
        
        if not all([amount, user_id, app]):
            return Response(
                {'error': 'amount, user_id, and app are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(id=user_id)
            amount_decimal = float(amount)
            
            rules = ComplianceRule.objects.filter(
                is_active=True,
                is_effective=True
            ).filter(
                Q(applicable_apps='all') | Q(applicable_apps=app)
            ).order_by('priority')
            
            evaluation_results = []
            triggered_rules = []
            
            for rule in rules:
                triggered = ComplianceService.evaluate_rule(
                    rule=rule,
                    amount=amount_decimal,
                    currency=currency,
                    user=user,
                    app=app
                )
                
                if triggered:
                    triggered_rules.append({
                        'rule_id': rule.rule_id,
                        'rule_name': rule.rule_name,
                        'action': rule.action,
                        'action_details': rule.action_details
                    })
                
                evaluation_results.append({
                    'rule_id': rule.rule_id,
                    'rule_name': rule.rule_name,
                    'triggered': triggered,
                    'action': rule.action if triggered else None
                })
            
            return Response({
                'success': True,
                'evaluation': evaluation_results,
                'triggered_rules': triggered_rules,
                'requires_review': any(r['action'] == 'review' for r in triggered_rules),
                'requires_escalation': any(r['action'] == 'escalate' for r in triggered_rules),
                'is_allowed': not any(r['action'] == 'deny' for r in triggered_rules)
            })
        
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Rule evaluation error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ComplianceAlertViewSet(viewsets.ModelViewSet):
    """
    API endpoint for compliance alerts
    """
    queryset = ComplianceAlert.objects.all()
    serializer_class = ComplianceAlertSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter alerts based on user role"""
        user = self.request.user
        
        if user.is_staff or user.groups.filter(name='Compliance Officers').exists():
            queryset = ComplianceAlert.objects.all()
        else:
            queryset = ComplianceAlert.objects.filter(
                Q(user=user) |
                Q(compliance_request__user=user) |
                Q(kyc_verification__user=user)
            )
        
        is_resolved = self.request.query_params.get('is_resolved')
        if is_resolved == 'true':
            queryset = queryset.filter(is_resolved=True)
        elif is_resolved == 'false':
            queryset = queryset.filter(is_resolved=False)
        
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        
        alert_type = self.request.query_params.get('alert_type')
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)
        
        queryset = queryset.order_by('is_resolved', '-created_at')
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acknowledge an alert"""
        alert = self.get_object()
        
        if alert.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        alert.is_acknowledged = True
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.save()
        
        AuditService.log_action(
            user=request.user,
            action=f"Acknowledged alert {alert.alert_id}",
            entity_type='alert',
            entity_id=alert.alert_id,
            old_value={'is_acknowledged': False},
            new_value={'is_acknowledged': True}
        )
        
        return Response({
            'success': True,
            'message': 'Alert acknowledged',
            'alert': self.get_serializer(alert).data
        })
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve an alert"""
        if not request.user.is_staff and not request.user.groups.filter(name='Compliance Officers').exists():
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        alert = self.get_object()
        resolution_notes = request.data.get('resolution_notes', '')
        
        alert.is_resolved = True
        alert.resolved_by = request.user
        alert.resolved_at = timezone.now()
        alert.resolution_notes = resolution_notes
        alert.save()
        
        AuditService.log_action(
            user=request.user,
            action=f"Resolved alert {alert.alert_id}",
            entity_type='alert',
            entity_id=alert.alert_id,
            old_value={'is_resolved': False},
            new_value={'is_resolved': True, 'resolution_notes': resolution_notes}
        )
        
        return Response({
            'success': True,
            'message': 'Alert resolved',
            'alert': self.get_serializer(alert).data
        })
    
    @action(detail=False, methods=['get'])
    def unresolved_count(self, request):
        """Get count of unresolved alerts"""
        count = self.get_queryset().filter(is_resolved=False).count()
        
        return Response({
            'success': True,
            'unresolved_count': count
        })


class ComplianceDashboardView(APIView):
    """
    API endpoint for compliance dashboard
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get comprehensive dashboard data"""
        try:
            if not request.user.is_staff and not request.user.groups.filter(name='Compliance Officers').exists():
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            today = timezone.now().date()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)
            
            stats = {
                'today': {
                    'requests': ComplianceRequest.objects.filter(created_at__date=today).count(),
                    'approved': ComplianceRequest.objects.filter(
                        created_at__date=today,
                        status='approved'
                    ).count(),
                    'rejected': ComplianceRequest.objects.filter(
                        created_at__date=today,
                        status='rejected'
                    ).count(),
                    'pending': ComplianceRequest.objects.filter(
                        created_at__date=today,
                        status='pending'
                    ).count(),
                },
                'this_week': {
                    'requests': ComplianceRequest.objects.filter(created_at__gte=week_ago).count(),
                    'kyc_submissions': KYCVerification.objects.filter(created_at__gte=week_ago).count(),
                    'kyc_approved': KYCVerification.objects.filter(
                        created_at__gte=week_ago,
                        verification_status='approved'
                    ).count(),
                },
                'this_month': {
                    'requests': ComplianceRequest.objects.filter(created_at__gte=month_ago).count(),
                    'video_calls': VideoCallSession.objects.filter(created_at__gte=month_ago).count(),
                    'tac_requests': TACRequest.objects.filter(created_at__gte=month_ago).count(),
                }
            }
            
            pending_by_priority = {
                'high': ComplianceRequest.objects.filter(status='pending', priority='high').count(),
                'normal': ComplianceRequest.objects.filter(status='pending', priority='normal').count(),
                'low': ComplianceRequest.objects.filter(status='pending', priority='low').count(),
            }
            
            requests_by_app = {}
            distinct_apps = ComplianceRequest.objects.values_list('app_name', flat=True).distinct()
            for app in distinct_apps:
                if app:
                    count = ComplianceRequest.objects.filter(app_name=app).count()
                    requests_by_app[app] = count
            
            recent_requests = ComplianceRequest.objects.order_by('-created_at')[:10]
            
            unresolved_alerts = ComplianceAlert.objects.filter(is_resolved=False).order_by('-severity', '-created_at')[:10]
            
            officer_workload = {}
            officers = User.objects.filter(
                Q(is_staff=True) | Q(groups__name='Compliance Officers')
            ).distinct()
            
            for officer in officers:
                assigned_count = ComplianceRequest.objects.filter(
                    assigned_to=officer,
                    status__in=['pending', 'under_review', 'info_required']
                ).count()
                completed_today = ComplianceRequest.objects.filter(
                    reviewed_by=officer,
                    resolved_at__date=today
                ).count()
                
                if assigned_count > 0 or completed_today > 0:
                    officer_workload[officer.email] = {
                        'assigned': assigned_count,
                        'completed_today': completed_today
                    }
            
            return Response({
                'success': True,
                'stats': stats,
                'pending_by_priority': pending_by_priority,
                'requests_by_app': requests_by_app,
                'officer_workload': officer_workload,
                'recent_requests': ComplianceRequestSerializer(recent_requests, many=True).data,
                'unresolved_alerts': ComplianceAlertSerializer(unresolved_alerts, many=True).data,
                'timestamp': timezone.now()
            })
        
        except Exception as e:
            logger.error(f"Dashboard error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ComplianceSearchView(APIView):
    """
    API endpoint for searching compliance data
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Search across compliance data"""
        query = request.query_params.get('q', '')
        
        if not query:
            return Response(
                {'error': 'Search query is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            results = {
                'compliance_requests': [],
                'kyc_verifications': [],
                'users': [],
                'total_count': 0
            }
            
            if request.user.is_staff or request.user.groups.filter(name='Compliance Officers').exists():
                requests = ComplianceRequest.objects.filter(
                    Q(compliance_id__icontains=query) |
                    Q(user__email__icontains=query) |
                    Q(user__first_name__icontains=query) |
                    Q(user__last_name__icontains=query) |
                    Q(description__icontains=query)
                )[:10]
                results['compliance_requests'] = ComplianceRequestSerializer(requests, many=True).data
                
                kyc_verifications = KYCVerification.objects.filter(
                    Q(kyc_id__icontains=query) |
                    Q(user__email__icontains=query) |
                    Q(first_name__icontains=query) |
                    Q(last_name__icontains=query) |
                    Q(id_number__icontains=query)
                )[:10]
                results['kyc_verifications'] = KYCVerificationSerializer(kyc_verifications, many=True).data
                
                users = User.objects.filter(
                    Q(email__icontains=query) |
                    Q(first_name__icontains=query) |
                    Q(last_name__icontains=query) |
                    Q(username__icontains=query)
                )[:10]
                results['users'] = UserSerializer(users, many=True).data
                
            else:
                requests = ComplianceRequest.objects.filter(user=request.user).filter(
                    Q(compliance_id__icontains=query) |
                    Q(description__icontains=query)
                )[:10]
                results['compliance_requests'] = ComplianceRequestSerializer(requests, many=True).data
                
                kyc_verifications = KYCVerification.objects.filter(user=request.user).filter(
                    Q(kyc_id__icontains=query) |
                    Q(first_name__icontains=query) |
                    Q(last_name__icontains=query)
                )[:10]
                results['kyc_verifications'] = KYCVerificationSerializer(kyc_verifications, many=True).data
            
            results['total_count'] = (
                len(results['compliance_requests']) +
                len(results['kyc_verifications']) +
                len(results['users'])
            )
            
            return Response({
                'success': True,
                'query': query,
                'results': results
            })
        
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def health_check(request):
    """Check compliance service health"""
    try:
        compliance_count = ComplianceRequest.objects.count()
        kyc_count = KYCVerification.objects.count()
        tac_count = TACRequest.objects.filter(is_used=False, is_expired=False, expires_at__gt=timezone.now()).count()
        
        services_status = {
            'database': 'OK',
            'compliance_service': 'OK',
            'kyc_service': 'OK',
            'tac_service': 'OK',
            'video_call_service': 'OK'
        }
        
        return Response({
            'status': 'healthy',
            'timestamp': timezone.now(),
            'services': services_status,
            'counts': {
                'compliance_requests': compliance_count,
                'kyc_verifications': kyc_count,
                'active_tac_codes': tac_count
            }
        })
    
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return Response(
            {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': timezone.now()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_compliance_request(request):
    """
    Endpoint for other apps to create compliance requests
    """
    serializer = ComplianceRequestCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        compliance_request = serializer.save()
        
        ComplianceService.assess_risk(compliance_request)
        
        if compliance_request.risk_level == 'low' and compliance_request.amount < 1000:
            compliance_request.status = 'approved'
            compliance_request.decision = 'approve'
            compliance_request.resolved_at = timezone.now()
            compliance_request.save()
            
            try:
                user = compliance_request.user
                user_name = f"{user.first_name} {user.last_name}" if user.first_name else user.email
                send_compliance_decision_email(
                    user.email,
                    user_name,
                    "Compliance Request Auto-Approved",
                    "approved",
                    f"Your compliance request {compliance_request.compliance_id} has been automatically approved."
                )
            except Exception as e:
                logger.error(f"Failed to send auto-approval email: {e}")
            
            AuditService.log_action(
                user=request.user,
                action='Compliance Request Auto-Approved',
                entity_type='compliance_request',
                entity_id=compliance_request.compliance_id,
                new_value={'status': 'approved', 'decision': 'approve'}
            )
        
        return Response({
            'success': True,
            'compliance_id': compliance_request.compliance_id,
            'status': compliance_request.status,
            'risk_level': compliance_request.risk_level,
            'requires_manual_review': compliance_request.requires_manual_review,
            'requires_tac': compliance_request.requires_tac,
            'requires_video_call': compliance_request.requires_video_call,
            'message': 'Compliance request created successfully'
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        logger.error(f"Compliance request creation error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_compliance_status(request, compliance_id):
    """Check status of a compliance request"""
    try:
        compliance_request = ComplianceRequest.objects.get(compliance_id=compliance_id)
        
        if compliance_request.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return Response({
            'success': True,
            'compliance_id': compliance_request.compliance_id,
            'status': compliance_request.status,
            'decision': compliance_request.decision,
            'risk_level': compliance_request.risk_level,
            'requires_tac': compliance_request.requires_tac,
            'requires_video_call': compliance_request.requires_video_call,
            'tac_verified': compliance_request.tac_verified_at is not None,
            'video_call_completed': compliance_request.video_call_completed_at is not None,
            'created_at': compliance_request.created_at,
            'resolved_at': compliance_request.resolved_at
        })
    
    except ComplianceRequest.DoesNotExist:
        return Response(
            {'error': 'Compliance request not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Compliance status check error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_tac_for_request(request, compliance_id):
    """Generate TAC for a compliance request"""
    try:
        compliance_request = ComplianceRequest.objects.get(compliance_id=compliance_id)
        
        if compliance_request.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        result = TACService.generate_tac(
            user=compliance_request.user,
            compliance_request=compliance_request,
            tac_type='compliance',
            purpose=f"Compliance request: {compliance_request.request_type}",
            amount=compliance_request.amount,
            currency=compliance_request.currency
        )
        
        if result['success']:
            compliance_request.tac_code = result['tac_code']
            compliance_request.tac_generated_at = timezone.now()
            compliance_request.status = 'awaiting_tac'
            compliance_request.save()
            
            return Response(result)
        else:
            return Response(
                {'error': result.get('error', 'TAC generation failed')},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except ComplianceRequest.DoesNotExist:
        return Response(
            {'error': 'Compliance request not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"TAC generation error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_tac_for_request(request, compliance_id):
    """Verify TAC for a compliance request"""
    try:
        compliance_request = ComplianceRequest.objects.get(compliance_id=compliance_id)
        
        if compliance_request.user != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        tac_code = request.data.get('tac_code')
        if not tac_code:
            return Response(
                {'error': 'TAC code is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = TACService.verify_tac(
            user=compliance_request.user,
            tac_code=tac_code,
            compliance_request_id=compliance_id
        )
        
        if result['success']:
            compliance_request.tac_verified_at = timezone.now()
            
            if (compliance_request.requires_tac and 
                not compliance_request.requires_video_call and 
                not compliance_request.requires_manual_review):
                compliance_request.status = 'under_review'
            
            compliance_request.save()
            
            return Response({
                'success': True,
                'message': 'TAC verified successfully',
                'compliance_id': compliance_request.compliance_id,
                'status': compliance_request.status,
                'next_steps': 'Waiting for compliance officer review' if compliance_request.requires_manual_review else 'Ready for processing'
            })
        else:
            return Response(
                {'error': result.get('error', 'TAC verification failed')},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except ComplianceRequest.DoesNotExist:
        return Response(
            {'error': 'Compliance request not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"TAC verification error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )