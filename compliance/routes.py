from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
import secrets
import hashlib
import os
import shutil
from pydantic import BaseModel, EmailStr, Field

from database import get_db
from compliance_models import (
    KYCVerification, KYCDocument, ComplianceCheck, TACCode,
    ComplianceAuditLog, WithdrawalRequest, VerificationStatus,
    DocumentType, ComplianceLevel
)

router = APIRouter(prefix="/api/compliance", tags=["compliance"])

# Pydantic Models
class KYCSubmissionRequest(BaseModel):
    user_id: str
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    date_of_birth: str
    nationality: str
    country_of_residence: str
    email: EmailStr
    phone_number: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state_province: Optional[str] = None
    postal_code: str
    id_number: str
    id_type: str
    occupation: Optional[str] = None
    source_of_funds: Optional[str] = None
    purpose_of_account: Optional[str] = None

class TACVerificationRequest(BaseModel):
    user_id: str
    code: str
    transaction_id: Optional[str] = None

class WithdrawalRequestModel(BaseModel):
    user_id: str
    amount: float
    currency: str = "USD"
    destination_type: str
    destination_details: dict

class DocumentUploadResponse(BaseModel):
    document_id: str
    file_name: str
    status: str
    message: str

# Utility Functions
def generate_tac_code() -> str:
    """Generate a 6-digit TAC code"""
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])

def hash_file(file_path: str) -> str:
    """Generate SHA256 hash of file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

async def save_upload_file(upload_file: UploadFile, user_id: str, doc_type: str) -> tuple:
    """Save uploaded file and return path and hash"""
    # Create user directory
    user_dir = f"uploads/kyc/{user_id}"
    os.makedirs(user_dir, exist_ok=True)
    
    # Generate unique filename
    file_extension = upload_file.filename.split(".")[-1]
    unique_filename = f"{doc_type}_{datetime.utcnow().timestamp()}.{file_extension}"
    file_path = os.path.join(user_dir, unique_filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    
    # Get file hash
    file_hash = hash_file(file_path)
    file_size = os.path.getsize(file_path)
    
    return file_path, file_hash, file_size

def log_compliance_action(
    db: Session,
    user_id: str,
    action: str,
    action_type: str,
    entity_type: str,
    entity_id: str,
    old_value: Optional[dict] = None,
    new_value: Optional[dict] = None,
    ip_address: Optional[str] = None
):
    """Log compliance actions for audit trail"""
    audit_log = ComplianceAuditLog(
        user_id=user_id,
        action=action,
        action_type=action_type,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address
    )
    db.add(audit_log)
    db.commit()

# Routes
@router.post("/kyc/submit")
async def submit_kyc(
    request: Request,
    kyc_data: KYCSubmissionRequest,
    db: Session = Depends(get_db)
):
    """Submit KYC verification request"""
    try:
        # Check if user already has pending verification
        existing = db.query(KYCVerification).filter(
            KYCVerification.user_id == kyc_data.user_id,
            KYCVerification.verification_status.in_([VerificationStatus.PENDING, VerificationStatus.IN_REVIEW])
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Verification already in progress")
        
        # Create new verification
        verification = KYCVerification(
            user_id=kyc_data.user_id,
            first_name=kyc_data.first_name,
            middle_name=kyc_data.middle_name,
            last_name=kyc_data.last_name,
            date_of_birth=datetime.fromisoformat(kyc_data.date_of_birth),
            nationality=kyc_data.nationality,
            country_of_residence=kyc_data.country_of_residence,
            email=kyc_data.email,
            phone_number=kyc_data.phone_number,
            address_line1=kyc_data.address_line1,
            address_line2=kyc_data.address_line2,
            city=kyc_data.city,
            state_province=kyc_data.state_province,
            postal_code=kyc_data.postal_code,
            id_number=kyc_data.id_number,
            id_type=DocumentType[kyc_data.id_type.upper()],
            occupation=kyc_data.occupation,
            source_of_funds=kyc_data.source_of_funds,
            purpose_of_account=kyc_data.purpose_of_account,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        db.add(verification)
        db.commit()
        db.refresh(verification)
        
        # Log action
        log_compliance_action(
            db,
            kyc_data.user_id,
            "KYC Submitted",
            "submission",
            "verification",
            verification.id,
            new_value={"status": "pending"},
            ip_address=request.client.host if request.client else None
        )
        
        return {
            "success": True,
            "verification_id": verification.id,
            "status": verification.verification_status,
            "message": "KYC verification submitted successfully"
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/kyc/upload-document")
async def upload_kyc_document(
    request: Request,
    verification_id: str = Form(...),
    user_id: str = Form(...),
    document_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload KYC document"""
    try:
        # Verify verification exists
        verification = db.query(KYCVerification).filter(
            KYCVerification.id == verification_id,
            KYCVerification.user_id == user_id
        ).first()
        
        if not verification:
            raise HTTPException(status_code=404, detail="Verification not found")
        
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/jpg", "application/pdf"]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        # Save file
        file_path, file_hash, file_size = await save_upload_file(file, user_id, document_type)
        
        # Create document record
        document = KYCDocument(
            verification_id=verification_id,
            user_id=user_id,
            document_type=DocumentType[document_type.upper()],
            file_name=os.path.basename(file_path),
            original_file_name=file.filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file.content_type,
            file_hash=file_hash
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Log action
        log_compliance_action(
            db,
            user_id,
            "Document Uploaded",
            "document_upload",
            "document",
            document.id,
            new_value={"type": document_type, "file_name": file.filename},
            ip_address=request.client.host if request.client else None
        )
        
        return DocumentUploadResponse(
            document_id=document.id,
            file_name=document.file_name,
            status="uploaded",
            message="Document uploaded successfully"
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/kyc/status/{user_id}")
async def get_kyc_status(user_id: str, db: Session = Depends(get_db)):
    """Get KYC verification status for user"""
    try:
        verification = db.query(KYCVerification).filter(
            KYCVerification.user_id == user_id
        ).order_by(KYCVerification.created_at.desc()).first()
        
        if not verification:
            return {
                "verified": False,
                "status": "not_started",
                "message": "KYC verification not initiated"
            }
        
        # Get documents
        documents = db.query(KYCDocument).filter(
            KYCDocument.verification_id == verification.id
        ).all()
        
        return {
            "verified": verification.verification_status == VerificationStatus.APPROVED,
            "status": verification.verification_status,
            "verification_id": verification.id,
            "compliance_level": verification.compliance_level,
            "risk_level": verification.risk_level,
            "documents": [
                {
                    "id": doc.id,
                    "type": doc.document_type,
                    "status": doc.status,
                    "uploaded_at": doc.uploaded_at.isoformat()
                }
                for doc in documents
            ],
            "created_at": verification.created_at.isoformat(),
            "verified_at": verification.verified_at.isoformat() if verification.verified_at else None
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tac/generate")
async def generate_tac(
    request: Request,
    user_id: str,
    transaction_id: Optional[str] = None,
    amount: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """Generate TAC code for transaction"""
    try:
        # Check for existing active TAC
        existing_tac = db.query(TACCode).filter(
            TACCode.user_id == user_id,
            TACCode.is_used == False,
            TACCode.is_expired == False,
            TACCode.expires_at > datetime.utcnow()
        ).first()
        
        if existing_tac:
            # Return existing code (in production, you'd send via email/SMS instead)
            return {
                "success": True,
                "message": "TAC code already sent",
                "expires_at": existing_tac.expires_at.isoformat(),
                "code": existing_tac.code  # Remove this in production!
            }
        
        # Generate new TAC
        code = generate_tac_code()
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        
        tac = TACCode(
            user_id=user_id,
            code=code,
            transaction_id=transaction_id,
            amount=amount,
            expires_at=expires_at,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        db.add(tac)
        db.commit()
        db.refresh(tac)
        
        # TODO: Send TAC via email/SMS
        # send_tac_email(user_email, code)
        
        return {
            "success": True,
            "message": "TAC code sent to your email",
            "tac_id": tac.id,
            "expires_at": expires_at.isoformat(),
            "code": code  # Remove this in production!
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tac/verify")
async def verify_tac(
    request: Request,
    data: TACVerificationRequest,
    db: Session = Depends(get_db)
):
    """Verify TAC code"""
    try:
        # Find TAC
        tac = db.query(TACCode).filter(
            TACCode.user_id == data.user_id,
            TACCode.code == data.code,
            TACCode.is_used == False,
            TACCode.is_expired == False
        ).first()
        
        if not tac:
            # Log failed attempt
            failed_tac = db.query(TACCode).filter(
                TACCode.user_id == data.user_id,
                TACCode.code == data.code
            ).first()
            
            if failed_tac:
                failed_tac.attempts += 1
                if failed_tac.attempts >= failed_tac.max_attempts:
                    failed_tac.is_expired = True
                db.commit()
            
            raise HTTPException(status_code=400, detail="Invalid or expired TAC code")
        
        # Check expiry
        if tac.expires_at < datetime.utcnow():
            tac.is_expired = True
            db.commit()
            raise HTTPException(status_code=400, detail="TAC code has expired")
        
        # Mark as used
        tac.is_used = True
        tac.used_at = datetime.utcnow()
        db.commit()
        
        # Log action
        log_compliance_action(
            db,
            data.user_id,
            "TAC Verified",
            "tac_verification",
            "tac",
            tac.id,
            new_value={"verified": True},
            ip_address=request.client.host if request.client else None
        )
        
        return {
            "success": True,
            "message": "TAC verified successfully",
            "verified_at": tac.used_at.isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/withdrawal/request")
async def request_withdrawal(
    request: Request,
    withdrawal: WithdrawalRequestModel,
    db: Session = Depends(get_db)
):
    """Request withdrawal"""
    try:
        # Check KYC status
        verification = db.query(KYCVerification).filter(
            KYCVerification.user_id == withdrawal.user_id,
            KYCVerification.verification_status == VerificationStatus.APPROVED
        ).first()
        
        if not verification:
            raise HTTPException(status_code=400, detail="KYC verification required")
        
        # Create withdrawal request
        withdrawal_req = WithdrawalRequest(
            user_id=withdrawal.user_id,
            amount=withdrawal.amount,
            currency=withdrawal.currency,
            destination_type=withdrawal.destination_type,
            destination_details=withdrawal.destination_details,
            kyc_status="verified"
        )
        
        db.add(withdrawal_req)
        db.commit()
        db.refresh(withdrawal_req)
        
        # Generate TAC
        tac_response = await generate_tac(
            request,
            withdrawal.user_id,
            withdrawal_req.id,
            withdrawal.amount,
            db
        )
        
        # Update withdrawal with TAC ID
        withdrawal_req.tac_code_id = tac_response.get("tac_id")
        withdrawal_req.status = "tac_sent"
        db.commit()
        
        return {
            "success": True,
            "withdrawal_id": withdrawal_req.id,
            "status": withdrawal_req.status,
            "tac_sent": True,
            "message": "Withdrawal request created. Please verify with TAC code."
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/verification/documents/{verification_id}")
async def get_verification_documents(
    verification_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get all documents for a verification"""
    try:
        verification = db.query(KYCVerification).filter(
            KYCVerification.id == verification_id,
            KYCVerification.user_id == user_id
        ).first()
        
        if not verification:
            raise HTTPException(status_code=404, detail="Verification not found")
        
        documents = db.query(KYCDocument).filter(
            KYCDocument.verification_id == verification_id
        ).all()
        
        return {
            "verification_id": verification_id,
            "documents": [
                {
                    "id": doc.id,
                    "type": doc.document_type,
                    "file_name": doc.original_file_name,
                    "status": doc.status,
                    "uploaded_at": doc.uploaded_at.isoformat(),
                    "verified_at": doc.verified_at.isoformat() if doc.verified_at else None
                }
                for doc in documents
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/audit-log/{user_id}")
async def get_audit_log(
    user_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get compliance audit log for user"""
    try:
        logs = db.query(ComplianceAuditLog).filter(
            ComplianceAuditLog.user_id == user_id
        ).order_by(ComplianceAuditLog.created_at.desc()).limit(limit).all()
        
        return {
            "user_id": user_id,
            "logs": [
                {
                    "id": log.id,
                    "action": log.action,
                    "action_type": log.action_type,
                    "entity_type": log.entity_type,
                    "created_at": log.created_at.isoformat(),
                    "ip_address": log.ip_address
                }
                for log in logs
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
