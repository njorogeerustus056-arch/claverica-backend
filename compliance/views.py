from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from django.db import transaction

from .models import (
    KYCVerification, KYCDocument, TACCode,
    ComplianceAuditLog, WithdrawalRequest, VerificationStatus
)
from .serializers import (
    KYCSubmissionSerializer, KYCVerificationSerializer,
    DocumentUploadSerializer, TACVerificationSerializer,
    WithdrawalRequestSerializer
)
from .services import (
    generate_tac_code, save_upload_file,
    log_compliance_action, get_client_ip
)
from .email_service import (
    send_tac_email, send_kyc_submitted_email,
    send_kyc_approved_email, send_withdrawal_confirmation_email
)


@api_view(['POST'])
def submit_kyc(request):
    """Submit KYC verification request"""
    serializer = KYCSubmissionSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    try:
        # Check if user already has pending verification
        existing = KYCVerification.objects.filter(
            user_id=data['user_id'],
            verification_status__in=[VerificationStatus.PENDING, VerificationStatus.IN_REVIEW]
        ).first()
        
        if existing:
            return Response(
                {"detail": "Verification already in progress"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create new verification
        verification = KYCVerification.objects.create(
            user_id=data['user_id'],
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
            user_agent=request.META.get('HTTP_USER_AGENT')
        )
        
        # Log action
        log_compliance_action(
            data['user_id'],
            "KYC Submitted",
            "submission",
            "verification",
            str(verification.id),
            new_value={"status": "pending"},
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
            "message": "KYC verification submitted successfully"
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        return Response(
            {"detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_kyc_document(request):
    """Upload KYC document"""
    serializer = DocumentUploadSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    try:
        # Verify verification exists
        verification = KYCVerification.objects.filter(
            id=data['verification_id'],
            user_id=data['user_id']
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
                {"detail": "Invalid file type"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Save file
        file_path, file_hash, file_size = save_upload_file(
            file,
            data['user_id'],
            data['document_type']
        )
        
        # Create document record
        document = KYCDocument.objects.create(
            verification=verification,
            user_id=data['user_id'],
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
            data['user_id'],
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


@api_view(['GET'])
def get_kyc_status(request, user_id):
    """Get KYC verification status for user"""
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


@api_view(['POST'])
def generate_tac(request):
    """Generate TAC code for transaction"""
    user_id = request.data.get('user_id')
    transaction_id = request.data.get('transaction_id')
    amount = request.data.get('amount')
    
    if not user_id:
        return Response(
            {"detail": "user_id is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
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
                "code": existing_tac.code  # Remove in production!
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
        
        # TODO: Get user email and send TAC
        # send_tac_email(user_email, code)
        
        return Response({
            "success": True,
            "message": "TAC code sent to your email",
            "tac_id": str(tac.id),
            "expires_at": expires_at.isoformat(),
            "code": code  # Remove in production!
        })
    
    except Exception as e:
        return Response(
            {"detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def verify_tac(request):
    """Verify TAC code"""
    serializer = TACVerificationSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    try:
        # Find TAC
        tac = TACCode.objects.filter(
            user_id=data['user_id'],
            code=data['code'],
            is_used=False,
            is_expired=False
        ).first()
        
        if not tac:
            # Log failed attempt
            failed_tac = TACCode.objects.filter(
                user_id=data['user_id'],
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
            data['user_id'],
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
            "verified_at": tac.used_at.isoformat()
        })
    
    except Exception as e:
        return Response(
            {"detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def request_withdrawal(request):
    """Request withdrawal"""
    serializer = WithdrawalRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    try:
        # Check KYC status
        verification = KYCVerification.objects.filter(
            user_id=data['user_id'],
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
                user_id=data['user_id'],
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
                user_id=data['user_id'],
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
            
            # TODO: Send TAC email
            # send_tac_email(user_email, code)
        
        return Response({
            "success": True,
            "withdrawal_id": str(withdrawal_req.id),
            "status": withdrawal_req.status,
            "tac_sent": True,
            "message": "Withdrawal request created. Please verify with TAC code.",
            "code": code  # Remove in production!
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        return Response(
            {"detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_verification_documents(request, verification_id):
    """Get all documents for a verification"""
    user_id = request.query_params.get('user_id')
    
    if not user_id:
        return Response(
            {"detail": "user_id is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
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
def get_audit_log(request, user_id):
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
