"""
compliance/views.py - Django REST Framework views for compliance app
"""

import logging  # ADD THIS LINE
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import api_view, parser_classes, permission_classes, action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.conf import settings

from .models import (
    KYCVerification, KYCDocument, TACCode,
    ComplianceAuditLog, WithdrawalRequest, VerificationStatus,
    DocumentType, ComplianceLevel
)
from .serializers import (
    KYCSubmissionSerializer, KYCVerificationSerializer,
    DocumentUploadSerializer, TACVerificationSerializer,
    WithdrawalRequestSerializer, WithdrawalModelSerializer,
    KYCDocumentSerializer, TACCodeSerializer,
    ComplianceAuditLogSerializer, KYCVerificationDetailSerializer
)
from .services import (
    generate_tac_code, save_upload_file,
    log_compliance_action, get_client_ip
)
from .email_service import (
    send_tac_email, send_kyc_submitted_email,
    send_kyc_approved_email, send_withdrawal_confirmation_email,
    send_kyc_rejected_email
)
from .permissions import IsOwnerOrAdmin, HasKYCApproved
from .utils import calculate_risk_score, validate_id_number, check_sanctions

logger = logging.getLogger(__name__)  # ADD THIS LINE
User = get_user_model()


class KYCVerificationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing KYC verifications
    """
    queryset = KYCVerification.objects.all()
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return KYCSubmissionSerializer
        elif self.action == 'retrieve':
            return KYCVerificationDetailSerializer
        return KYCVerificationSerializer
    
    def get_queryset(self):
        """
        Users can only see their own verifications
        Admins can see all verifications
        """
        user = self.request.user
        if user.is_staff:
            return KYCVerification.objects.all()
        return KYCVerification.objects.filter(user_id=str(user.id))
    
    def create(self, request):
        """Submit KYC verification request"""
        serializer = KYCSubmissionSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        user_id = str(request.user.id)
        
        try:
            # Check if user already has pending verification
            existing = KYCVerification.objects.filter(
                user_id=user_id,
                verification_status__in=[VerificationStatus.PENDING, VerificationStatus.IN_REVIEW]
            ).first()
            
            if existing:
                return Response(
                    {"detail": "Verification already in progress"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Calculate risk score
            risk_score, risk_level = calculate_risk_score(data)
            
            # Check sanctions (simplified)
            if check_sanctions(f"{data['first_name']} {data['last_name']}", data['country_of_residence']):
                risk_score += 50
                risk_level = 'high'
            
            # Validate ID number
            if not validate_id_number(data['id_number'], data['id_type']):
                return Response(
                    {"detail": "Invalid ID number format"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create new verification
            verification = KYCVerification.objects.create(
                user_id=user_id,
                first_name=data['first_name'],
                middle_name=data.get('middle_name'),
                last_name=data['last_name'],
                date_of_birth=data['date_of_birth'],
                nationality=data['nationality'],
                country_of_residence=data['country_of_residence'],
                email=data['email'],
                phone_number=data['phone_number'],
                address_line1=data['address_line1'],
                address_line2=data.get('address_line2'),
                city=data['city'],
                state_province=data.get('state_province'),
                postal_code=data['postal_code'],
                id_number=data['id_number'],
                id_type=data['id_type'],
                occupation=data.get('occupation'),
                source_of_funds=data.get('source_of_funds'),
                purpose_of_account=data.get('purpose_of_account'),
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                risk_score=risk_score,
                risk_level=risk_level
            )
            
            # Log action
            log_compliance_action(
                user_id,
                "KYC Submitted",
                "submission",
                "verification",
                str(verification.id),
                new_value={"status": "pending", "risk_level": risk_level},
                ip_address=get_client_ip(request)
            )
            
            # Send confirmation email
            send_kyc_submitted_email(
                data['email'],
                data['first_name'],
                str(verification.id)
            )
            
            return Response({
                "success": True,
                "verification_id": str(verification.id),
                "status": verification.verification_status,
                "risk_level": verification.risk_level,
                "message": "KYC verification submitted successfully"
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a KYC verification (admin only)"""
        if not request.user.is_staff:
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        verification = self.get_object()
        
        if verification.verification_status != VerificationStatus.PENDING:
            return Response(
                {"detail": "Verification is not pending"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        verification.verification_status = VerificationStatus.APPROVED
        verification.verified_by = str(request.user.id)
        verification.verified_at = timezone.now()
        verification.save()
        
        # Send approval email
        send_kyc_approved_email(
            verification.email,
            f"{verification.first_name} {verification.last_name}",
            verification.compliance_level
        )
        
        # Log action
        log_compliance_action(
            str(request.user.id),
            "KYC Approved",
            "approval",
            "verification",
            str(verification.id),
            old_value={"status": "pending"},
            new_value={"status": "approved"},
            ip_address=get_client_ip(request)
        )
        
        return Response({
            "success": True,
            "message": "KYC verification approved successfully",
            "verification": KYCVerificationSerializer(verification).data
        })
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a KYC verification (admin only)"""
        if not request.user.is_staff:
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        verification = self.get_object()
        rejection_reason = request.data.get('rejection_reason', '')
        
        if not rejection_reason:
            return Response(
                {"detail": "Rejection reason is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        verification.verification_status = VerificationStatus.REJECTED
        verification.rejection_reason = rejection_reason
        verification.verified_by = str(request.user.id)
        verification.verified_at = timezone.now()
        verification.save()
        
        # Send rejection email
        send_kyc_rejected_email(
            verification.email,
            f"{verification.first_name} {verification.last_name}",
            rejection_reason
        )
        
        # Log action
        log_compliance_action(
            str(request.user.id),
            "KYC Rejected",
            "rejection",
            "verification",
            str(verification.id),
            old_value={"status": "pending"},
            new_value={"status": "rejected", "reason": rejection_reason},
            ip_address=get_client_ip(request)
        )
        
        return Response({
            "success": True,
            "message": "KYC verification rejected",
            "verification": KYCVerificationSerializer(verification).data
        })
    
    @action(detail=False, methods=['get'])
    def my_status(self, request):
        """Get current user's KYC status"""
        user_id = str(request.user.id)
        
        try:
            verification = KYCVerification.objects.filter(
                user_id=user_id
            ).order_by('-created_at').first()
            
            if not verification:
                return Response({
                    "verified": False,
                    "status": "not_started",
                    "message": "KYC verification not initiated"
                })
            
            # Get documents
            documents = KYCDocument.objects.filter(verification=verification)
            
            return Response({
                "verified": verification.verification_status == VerificationStatus.APPROVED,
                "status": verification.verification_status,
                "verification_id": str(verification.id),
                "compliance_level": verification.compliance_level,
                "risk_level": verification.risk_level,
                "documents": [
                    {
                        "id": str(doc.id),
                        "type": doc.document_type,
                        "status": doc.status,
                        "uploaded_at": doc.uploaded_at.isoformat()
                    }
                    for doc in documents
                ],
                "created_at": verification.created_at.isoformat(),
                "verified_at": verification.verified_at.isoformat() if verification.verified_at else None
            })
        
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class KYCDocumentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing KYC documents
    """
    queryset = KYCDocument.objects.all()
    serializer_class = KYCDocumentSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return KYCDocument.objects.all()
        return KYCDocument.objects.filter(user_id=str(user.id))
    
    def create(self, request):
        """Upload KYC document"""
        serializer = DocumentUploadSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        user_id = str(request.user.id)
        
        try:
            # Verify verification exists and belongs to user
            verification = KYCVerification.objects.filter(
                id=data['verification_id'],
                user_id=user_id
            ).first()
            
            if not verification:
                return Response(
                    {"detail": "Verification not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Validate file type
            file = data['file']
            allowed_types = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf']
            if file.content_type not in allowed_types:
                return Response(
                    {"detail": "Invalid file type. Allowed: JPEG, PNG, PDF"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check file size (10MB limit)
            max_size = 10 * 1024 * 1024  # 10MB
            if file.size > max_size:
                return Response(
                    {"detail": "File too large. Maximum size is 10MB"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Save file
            file_path, file_hash, file_size = save_upload_file(
                file,
                user_id,
                data['document_type']
            )
            
            # Create document record
            document = KYCDocument.objects.create(
                verification=verification,
                user_id=user_id,
                document_type=data['document_type'],
                file_name=file_path.split('/')[-1],
                original_file_name=file.name,
                file_path=file_path,
                file_size=file_size,
                file_type=file.content_type,
                file_hash=file_hash
            )
            
            # Log action
            log_compliance_action(
                user_id,
                "Document Uploaded",
                "document_upload",
                "document",
                str(document.id),
                new_value={"type": data['document_type'], "file_name": file.name},
                ip_address=get_client_ip(request)
            )
            
            return Response({
                "document_id": str(document.id),
                "file_name": document.file_name,
                "status": "uploaded",
                "message": "Document uploaded successfully"
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download a document"""
        document = self.get_object()
        
        # Only allow download if user owns the document or is staff
        if not request.user.is_staff and str(document.user_id) != str(request.user.id):
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # In a real app, you would serve the file here
        # For now, return the file path
        return Response({
            "file_path": document.file_path,
            "file_name": document.original_file_name,
            "file_type": document.file_type
        })


class TACCodeViewSet(viewsets.ViewSet):
    """
    API endpoint for TAC code operations
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate TAC code for transaction"""
        user_id = str(request.user.id)
        transaction_id = request.data.get('transaction_id')
        amount = request.data.get('amount')
        
        # Rate limiting check
        cache_key = f"tac_generate:{user_id}"
        request_count = cache.get(cache_key, 0)
        
        max_requests = getattr(settings, 'TAC_MAX_REQUESTS_PER_HOUR', 10)
        if request_count >= max_requests:
            return Response({
                "error": "Rate limit exceeded",
                "message": f"Maximum {max_requests} TAC requests per hour allowed",
                "retry_after": cache.ttl(cache_key) if cache.ttl(cache_key) else 3600
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        try:
            # Check for existing active TAC
            existing_tac = TACCode.objects.filter(
                user_id=user_id,
                is_used=False,
                is_expired=False,
                expires_at__gt=timezone.now()
            ).first()
            
            if existing_tac:
                return Response({
                    "success": True,
                    "message": "TAC code already sent",
                    "expires_at": existing_tac.expires_at.isoformat(),
                    "time_remaining": (existing_tac.expires_at - timezone.now()).total_seconds(),
                    "code": existing_tac.code if settings.DEBUG else None  # Only show in debug mode
                })
            
            # Generate new TAC
            code = generate_tac_code()
            expires_at = timezone.now() + timedelta(minutes=5)
            
            tac = TACCode.objects.create(
                user_id=user_id,
                code=code,
                transaction_id=transaction_id,
                amount=amount,
                expires_at=expires_at,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            
            # Increment rate limit counter
            cache.set(cache_key, request_count + 1, timeout=3600)
            
            # Get user email and send TAC
            try:
                user = User.objects.get(id=user_id)
                send_tac_email(user.email, code, user.get_full_name() or user.username)
            except Exception as email_error:
                logger.error(f"Failed to send TAC email: {email_error}")
                # Continue even if email fails
            
            return Response({
                "success": True,
                "message": "TAC code sent to your email",
                "tac_id": str(tac.id),
                "expires_at": expires_at.isoformat(),
                "time_remaining": 300,  # 5 minutes in seconds
                "code": code if settings.DEBUG else None  # Only show in debug mode
            })
        
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def verify(self, request):
        """Verify TAC code"""
        serializer = TACVerificationSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        user_id = str(request.user.id)
        
        try:
            # Find TAC
            tac = TACCode.objects.filter(
                user_id=user_id,
                code=data['code'],
                is_used=False,
                is_expired=False
            ).first()
            
            if not tac:
                # Log failed attempt
                failed_tac = TACCode.objects.filter(
                    user_id=user_id,
                    code=data['code']
                ).first()
                
                if failed_tac:
                    failed_tac.attempts += 1
                    if failed_tac.attempts >= failed_tac.max_attempts:
                        failed_tac.is_expired = True
                    failed_tac.save()
                
                return Response(
                    {"detail": "Invalid or expired TAC code"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check expiry
            if tac.expires_at < timezone.now():
                tac.is_expired = True
                tac.save()
                return Response(
                    {"detail": "TAC code has expired"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Mark as used
            tac.is_used = True
            tac.used_at = timezone.now()
            tac.save()
            
            # Log action
            log_compliance_action(
                user_id,
                "TAC Verified",
                "tac_verification",
                "tac",
                str(tac.id),
                new_value={"verified": True},
                ip_address=get_client_ip(request)
            )
            
            return Response({
                "success": True,
                "message": "TAC verified successfully",
                "verified_at": tac.used_at.isoformat(),
                "transaction_id": tac.transaction_id
            })
        
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WithdrawalRequestViewSet(viewsets.ModelViewSet):
    """
    API endpoint for withdrawal requests
    """
    queryset = WithdrawalRequest.objects.all()
    serializer_class = WithdrawalModelSerializer
    permission_classes = [IsAuthenticated, HasKYCApproved]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return WithdrawalRequest.objects.all()
        return WithdrawalRequest.objects.filter(user_id=str(user.id))
    
    def create(self, request):
        """Request withdrawal"""
        serializer = WithdrawalRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        user_id = str(request.user.id)
        
        try:
            # Check KYC status
            verification = KYCVerification.objects.filter(
                user_id=user_id,
                verification_status=VerificationStatus.APPROVED
            ).first()
            
            if not verification:
                return Response(
                    {"detail": "KYC verification required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            with transaction.atomic():
                # Create withdrawal request
                withdrawal_req = WithdrawalRequest.objects.create(
                    user_id=user_id,
                    amount=data['amount'],
                    currency=data['currency'],
                    destination_type=data['destination_type'],
                    destination_details=data['destination_details'],
                    kyc_status="verified"
                )
                
                # Generate TAC
                code = generate_tac_code()
                expires_at = timezone.now() + timedelta(minutes=5)
                
                tac = TACCode.objects.create(
                    user_id=user_id,
                    code=code,
                    transaction_id=str(withdrawal_req.id),
                    amount=data['amount'],
                    expires_at=expires_at,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT')
                )
                
                # Update withdrawal with TAC ID
                withdrawal_req.tac_code_id = str(tac.id)
                withdrawal_req.status = "tac_sent"
                withdrawal_req.save()
                
                # Send TAC email
                try:
                    user = User.objects.get(id=user_id)
                    send_tac_email(user.email, code, user.get_full_name() or user.username)
                except Exception as email_error:
                    logger.error(f"Failed to send TAC email: {email_error}")
                    # Continue even if email fails
            
            return Response({
                "success": True,
                "withdrawal_id": str(withdrawal_req.id),
                "status": withdrawal_req.status,
                "tac_sent": True,
                "message": "Withdrawal request created. Please verify with TAC code.",
                "code": code if settings.DEBUG else None  # Only show in debug mode
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def verify_tac(self, request, pk=None):
        """Verify TAC for withdrawal"""
        withdrawal = self.get_object()
        code = request.data.get('code')
        
        if not code:
            return Response(
                {"detail": "TAC code is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Find and verify TAC
            tac = TACCode.objects.filter(
                id=withdrawal.tac_code_id,
                code=code,
                is_used=False,
                is_expired=False
            ).first()
            
            if not tac:
                return Response(
                    {"detail": "Invalid TAC code"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if tac.expires_at < timezone.now():
                tac.is_expired = True
                tac.save()
                return Response(
                    {"detail": "TAC code has expired"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Mark TAC as used
            tac.is_used = True
            tac.used_at = timezone.now()
            tac.save()
            
            # Update withdrawal status
            withdrawal.tac_verified = True
            withdrawal.status = "processing"
            withdrawal.save()
            
            # Log action
            log_compliance_action(
                withdrawal.user_id,
                "Withdrawal TAC Verified",
                "tac_verification",
                "withdrawal",
                str(withdrawal.id),
                new_value={"status": "processing"},
                ip_address=get_client_ip(request)
            )
            
            # Send confirmation email
            try:
                user = User.objects.get(id=withdrawal.user_id)
                send_withdrawal_confirmation_email(
                    user.email,
                    user.get_full_name() or user.username,
                    withdrawal.amount,
                    withdrawal.currency
                )
            except Exception as email_error:
                logger.error(f"Failed to send withdrawal confirmation email: {email_error}")
            
            return Response({
                "success": True,
                "message": "Withdrawal verified and is being processed",
                "withdrawal_id": str(withdrawal.id),
                "status": withdrawal.status
            })
        
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a withdrawal request"""
        withdrawal = self.get_object()
        
        if withdrawal.status not in ['pending', 'tac_sent']:
            return Response(
                {"detail": "Cannot cancel withdrawal in current status"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        withdrawal.status = "cancelled"
        withdrawal.save()
        
        # Log action
        log_compliance_action(
            withdrawal.user_id,
            "Withdrawal Cancelled",
            "cancellation",
            "withdrawal",
            str(withdrawal.id),
            old_value={"status": withdrawal._original_status if hasattr(withdrawal, '_original_status') else "unknown"},
            new_value={"status": "cancelled"}
        )
        
        return Response({
            "success": True,
            "message": "Withdrawal cancelled successfully"
        })


class ComplianceAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing compliance audit logs
    """
    queryset = ComplianceAuditLog.objects.all()
    serializer_class = ComplianceAuditLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return ComplianceAuditLog.objects.all()
        return ComplianceAuditLog.objects.filter(user_id=str(user.id))


# Legacy function-based views (for backward compatibility)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_kyc_legacy(request):
    """Legacy KYC submission endpoint"""
    viewset = KYCVerificationViewSet()
    viewset.request = request
    viewset.format_kwarg = None
    return viewset.create(request)


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([IsAuthenticated])
def upload_kyc_document_legacy(request):
    """Legacy document upload endpoint"""
    viewset = KYCDocumentViewSet()
    viewset.request = request
    viewset.format_kwarg = None
    return viewset.create(request)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_kyc_status_legacy(request, user_id):
    """Legacy KYC status endpoint"""
    viewset = KYCVerificationViewSet()
    viewset.request = request
    viewset.format_kwarg = None
    viewset.kwargs = {'pk': user_id}
    return viewset.my_status(request)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_tac_legacy(request):
    """Legacy TAC generation endpoint"""
    viewset = TACCodeViewSet()
    viewset.request = request
    viewset.format_kwarg = None
    return viewset.generate(request)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_tac_legacy(request):
    """Legacy TAC verification endpoint"""
    viewset = TACCodeViewSet()
    viewset.request = request
    viewset.format_kwarg = None
    return viewset.verify(request)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_withdrawal_legacy(request):
    """Legacy withdrawal request endpoint"""
    viewset = WithdrawalRequestViewSet()
    viewset.request = request
    viewset.format_kwarg = None
    return viewset.create(request)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_verification_documents_legacy(request, verification_id):
    """Get all documents for a verification"""
    user_id = str(request.user.id)
    
    try:
        verification = KYCVerification.objects.filter(
            id=verification_id,
            user_id=user_id
        ).first()
        
        if not verification:
            return Response(
                {"detail": "Verification not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        documents = KYCDocument.objects.filter(verification=verification)
        
        return Response({
            "verification_id": str(verification_id),
            "documents": [
                {
                    "id": str(doc.id),
                    "type": doc.document_type,
                    "file_name": doc.original_file_name,
                    "status": doc.status,
                    "uploaded_at": doc.uploaded_at.isoformat(),
                    "verified_at": doc.verified_at.isoformat() if doc.verified_at else None
                }
                for doc in documents
            ]
        })
    
    except Exception as e:
        return Response(
            {"detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_audit_log_legacy(request, user_id):
    """Get compliance audit log for user"""
    limit = int(request.query_params.get('limit', 50))
    
    try:
        logs = ComplianceAuditLog.objects.filter(
            user_id=user_id
        ).order_by('-created_at')[:limit]
        
        return Response({
            "user_id": user_id,
            "logs": [
                {
                    "id": str(log.id),
                    "action": log.action,
                    "action_type": log.action_type,
                    "entity_type": log.entity_type,
                    "created_at": log.created_at.isoformat(),
                    "ip_address": log.ip_address
                }
                for log in logs
            ]
        })
    
    except Exception as e:
        return Response(
            {"detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Dashboard views
class ComplianceDashboardView(APIView):
    """Compliance dashboard for admins"""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Get compliance dashboard statistics"""
        try:
            total_verifications = KYCVerification.objects.count()
            pending_verifications = KYCVerification.objects.filter(
                verification_status=VerificationStatus.PENDING
            ).count()
            approved_verifications = KYCVerification.objects.filter(
                verification_status=VerificationStatus.APPROVED
            ).count()
            
            recent_withdrawals = WithdrawalRequest.objects.order_by('-created_at')[:10]
            
            return Response({
                "statistics": {
                    "total_verifications": total_verifications,
                    "pending_verifications": pending_verifications,
                    "approved_verifications": approved_verifications,
                    "rejected_verifications": KYCVerification.objects.filter(
                        verification_status=VerificationStatus.REJECTED
                    ).count(),
                    "total_withdrawals": WithdrawalRequest.objects.count(),
                    "pending_withdrawals": WithdrawalRequest.objects.filter(
                        status='pending'
                    ).count(),
                    "completed_withdrawals": WithdrawalRequest.objects.filter(
                        status='completed'
                    ).count(),
                },
                "recent_activity": {
                    "withdrawals": WithdrawalModelSerializer(recent_withdrawals, many=True).data,
                    "tac_codes": TACCode.objects.order_by('-created_at')[:10].count(),
                    "audit_logs": ComplianceAuditLog.objects.order_by('-created_at')[:10].count(),
                }
            })
        
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserComplianceStatusView(APIView):
    """Get comprehensive compliance status for a user"""
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    
    def get(self, request, user_id=None):
        """Get user compliance status"""
        if user_id is None:
            user_id = str(request.user.id)
        
        try:
            # Get KYC verification
            verification = KYCVerification.objects.filter(
                user_id=user_id
            ).order_by('-created_at').first()
            
            # Get documents
            documents = []
            if verification:
                documents = KYCDocument.objects.filter(verification=verification)
            
            # Get withdrawal history
            withdrawals = WithdrawalRequest.objects.filter(
                user_id=user_id
            ).order_by('-created_at')[:10]
            
            # Get audit logs
            audit_logs = ComplianceAuditLog.objects.filter(
                user_id=user_id
            ).order_by('-created_at')[:20]
            
            return Response({
                "user_id": user_id,
                "kyc": {
                    "verified": verification.verification_status == VerificationStatus.APPROVED if verification else False,
                    "status": verification.verification_status if verification else "not_started",
                    "compliance_level": verification.compliance_level if verification else None,
                    "risk_level": verification.risk_level if verification else None,
                    "documents_count": documents.count(),
                    "documents_approved": documents.filter(status=VerificationStatus.APPROVED).count(),
                    "verification_date": verification.verified_at.isoformat() if verification and verification.verified_at else None,
                },
                "withdrawals": {
                    "total": withdrawals.count(),
                    "pending": withdrawals.filter(status='pending').count(),
                    "completed": withdrawals.filter(status='completed').count(),
                    "recent": WithdrawalModelSerializer(withdrawals, many=True).data
                },
                "audit_logs": {
                    "total": audit_logs.count(),
                    "recent": ComplianceAuditLogSerializer(audit_logs, many=True).data
                }
            })
        
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )