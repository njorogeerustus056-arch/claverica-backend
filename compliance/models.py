from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Float, JSON, Enum as SQLEnum, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base
import enum
import uuid

class VerificationStatus(str, enum.Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

class DocumentType(str, enum.Enum):
    PASSPORT = "passport"
    NATIONAL_ID = "national_id"
    DRIVERS_LICENSE = "drivers_license"
    UTILITY_BILL = "utility_bill"
    BANK_STATEMENT = "bank_statement"
    SELFIE = "selfie"

class ComplianceLevel(str, enum.Enum):
    BASIC = "basic"
    STANDARD = "standard"
    ENHANCED = "enhanced"
    PREMIUM = "premium"

class KYCVerification(Base):
    __tablename__ = "kyc_verifications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    
    # Personal Information
    first_name = Column(String, nullable=False)
    middle_name = Column(String, nullable=True)
    last_name = Column(String, nullable=False)
    date_of_birth = Column(DateTime, nullable=False)
    nationality = Column(String, nullable=False)
    country_of_residence = Column(String, nullable=False)
    
    # Contact Information
    email = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    address_line1 = Column(String, nullable=False)
    address_line2 = Column(String, nullable=True)
    city = Column(String, nullable=False)
    state_province = Column(String, nullable=True)
    postal_code = Column(String, nullable=False)
    
    # Identity Verification
    id_number = Column(String, nullable=False)
    id_type = Column(SQLEnum(DocumentType), nullable=False)
    id_issue_date = Column(DateTime, nullable=True)
    id_expiry_date = Column(DateTime, nullable=True)
    
    # Compliance Level
    compliance_level = Column(SQLEnum(ComplianceLevel), default=ComplianceLevel.BASIC)
    verification_status = Column(SQLEnum(VerificationStatus), default=VerificationStatus.PENDING)
    
    # Risk Assessment
    risk_score = Column(Float, default=0.0)
    risk_level = Column(String, default="low")  # low, medium, high
    
    # Verification Details
    verified_by = Column(String, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Additional Data
    occupation = Column(String, nullable=True)
    source_of_funds = Column(String, nullable=True)
    purpose_of_account = Column(String, nullable=True)
    expected_transaction_volume = Column(String, nullable=True)
    
    # Metadata
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    geolocation = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    documents = relationship("KYCDocument", back_populates="verification", cascade="all, delete-orphan")
    compliance_checks = relationship("ComplianceCheck", back_populates="verification", cascade="all, delete-orphan")


class KYCDocument(Base):
    __tablename__ = "kyc_documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    verification_id = Column(String, ForeignKey("kyc_verifications.id"), nullable=False)
    user_id = Column(String, nullable=False, index=True)
    
    # Document Details
    document_type = Column(SQLEnum(DocumentType), nullable=False)
    document_number = Column(String, nullable=True)
    
    # File Information
    file_name = Column(String, nullable=False)
    original_file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String, nullable=False)
    file_hash = Column(String, nullable=True)
    
    # Verification Status
    status = Column(SQLEnum(VerificationStatus), default=VerificationStatus.PENDING)
    verified_at = Column(DateTime, nullable=True)
    verified_by = Column(String, nullable=True)
    
    # OCR & Analysis
    ocr_data = Column(JSON, nullable=True)
    extracted_data = Column(JSON, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    verification = relationship("KYCVerification", back_populates="documents")


class ComplianceCheck(Base):
    __tablename__ = "compliance_checks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    verification_id = Column(String, ForeignKey("kyc_verifications.id"), nullable=False)
    user_id = Column(String, nullable=False, index=True)
    
    # Check Details
    check_type = Column(String, nullable=False)  # aml, sanctions, pep, adverse_media
    status = Column(String, nullable=False)  # pass, fail, review
    result = Column(JSON, nullable=True)
    
    # Risk Information
    risk_score = Column(Float, default=0.0)
    matches_found = Column(Integer, default=0)
    
    # Provider Information
    provider = Column(String, nullable=True)
    provider_reference = Column(String, nullable=True)
    
    # Timestamps
    checked_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Relationships
    verification = relationship("KYCVerification", back_populates="compliance_checks")


class TACCode(Base):
    __tablename__ = "tac_codes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    
    # Code Details
    code = Column(String(6), nullable=False)
    code_type = Column(String, default="withdrawal")  # withdrawal, transfer, verification
    
    # Validation
    is_used = Column(Boolean, default=False)
    is_expired = Column(Boolean, default=False)
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    
    # Associated Data
    transaction_id = Column(String, nullable=True)
    amount = Column(Float, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    
    # IP & Security
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)


class ComplianceAuditLog(Base):
    __tablename__ = "compliance_audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    verification_id = Column(String, nullable=True)
    
    # Action Details
    action = Column(String, nullable=False)
    action_type = Column(String, nullable=False)  # document_upload, status_change, check_run
    entity_type = Column(String, nullable=False)  # verification, document, check
    entity_id = Column(String, nullable=False)
    
    # Changes
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    
    # Actor Information
    actor_id = Column(String, nullable=True)  # admin/system that made the change
    actor_role = Column(String, nullable=True)
    
    # Request Information
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Notes
    notes = Column(Text, nullable=True)


class WithdrawalRequest(Base):
    __tablename__ = "withdrawal_requests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    
    # Amount Details
    amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    
    # Destination
    destination_type = Column(String, nullable=False)  # bank, crypto, payment_platform
    destination_details = Column(JSON, nullable=False)
    
    # Status
    status = Column(String, default="pending")  # pending, tac_sent, approved, processing, completed, rejected
    
    # Compliance
    requires_tac = Column(Boolean, default=True)
    tac_verified = Column(Boolean, default=False)
    tac_code_id = Column(String, nullable=True)
    
    kyc_status = Column(String, nullable=True)
    compliance_status = Column(String, default="pending")
    
    # Processing
    processed_by = Column(String, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    transaction_hash = Column(String, nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
