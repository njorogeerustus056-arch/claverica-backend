import secrets
import hashlib
import os
from datetime import timedelta
from django.utils import timezone
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import (
    KYCVerification, KYCDocument, TACCode,
    ComplianceAuditLog, VerificationStatus
)


def generate_tac_code():
    """Generate a 6-digit TAC code"""
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])


def hash_file(file_path):
    """Generate SHA256 hash of file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def save_upload_file(upload_file, user_id, doc_type):
    """Save uploaded file and return path and hash"""
    # Create user directory
    user_dir = f"uploads/kyc/{user_id}"
    os.makedirs(user_dir, exist_ok=True)
    
    # Generate unique filename
    file_extension = upload_file.name.split(".")[-1]
    unique_filename = f"{doc_type}_{timezone.now().timestamp()}.{file_extension}"
    file_path = os.path.join(user_dir, unique_filename)
    
    # Save file using Django storage
    path = default_storage.save(file_path, ContentFile(upload_file.read()))
    full_path = default_storage.path(path)
    
    # Get file hash
    file_hash = hash_file(full_path)
    file_size = upload_file.size
    
    return path, file_hash, file_size


def log_compliance_action(user_id, action, action_type, entity_type, entity_id,
                         old_value=None, new_value=None, ip_address=None):
    """Log compliance actions for audit trail"""
    ComplianceAuditLog.objects.create(
        user_id=user_id,
        action=action,
        action_type=action_type,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address
    )


def get_client_ip(request):
    """Extract client IP from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
