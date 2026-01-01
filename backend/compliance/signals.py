"""
compliance/signals.py - Signal handlers for compliance app
"""

from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth import get_user_model
import logging

from .models import (
    KYCVerification, KYCDocument, TACCode,
    WithdrawalRequest, VerificationStatus,
    ComplianceAuditLog, ComplianceCheck
)
from .services import (
    perform_compliance_checks,
    log_compliance_action,
    cleanup_expired_tac_codes
)
from .email_service import send_kyc_approved_email

logger = logging.getLogger(__name__)
User = get_user_model()


@receiver(post_save, sender=KYCVerification)
def handle_kyc_verification_save(sender, instance, created, **kwargs):
    """
    Handle KYC verification save events
    """
    if created:
        # New verification created
        logger.info(f"New KYC verification created: {instance.id} for user {instance.user_id}")
        
        # Perform automated compliance checks
        perform_compliance_checks(instance.id)
        
        # Log the creation
        log_compliance_action(
            instance.user_id,
            "KYC Verification Created",
            "creation",
            "verification",
            str(instance.id),
            new_value={
                "status": instance.verification_status,
                "risk_level": instance.risk_level
            }
        )
    
    else:
        # Verification updated - FIXED HERE
        update_fields = kwargs.get('update_fields', None)
        
        # Check if update_fields exists and contains 'verification_status'
        if update_fields and 'verification_status' in update_fields:
            # Status changed
            old_status = instance._old_verification_status if hasattr(instance, '_old_verification_status') else None
            
            if instance.verification_status == VerificationStatus.APPROVED:
                logger.info(f"KYC verification approved: {instance.id}")
                
                # Send approval email
                try:
                    send_kyc_approved_email(
                        instance.email,
                        f"{instance.first_name} {instance.last_name}",
                        instance.compliance_level
                    )
                except Exception as e:
                    logger.error(f"Failed to send KYC approval email: {e}")
            
            elif instance.verification_status == VerificationStatus.REJECTED:
                logger.info(f"KYC verification rejected: {instance.id}")
            
            # Log status change
            log_compliance_action(
                instance.user_id,
                "KYC Status Changed",
                "status_change",
                "verification",
                str(instance.id),
                old_value={"status": old_status} if old_status else None,
                new_value={"status": instance.verification_status}
            )


@receiver(pre_save, sender=KYCVerification)
def capture_kyc_verification_changes(sender, instance, **kwargs):
    """
    Capture old values before saving KYC verification
    """
    if instance.pk:
        try:
            old_instance = KYCVerification.objects.get(pk=instance.pk)
            instance._old_verification_status = old_instance.verification_status
        except KYCVerification.DoesNotExist:
            pass


@receiver(post_save, sender=KYCDocument)
def handle_document_upload(sender, instance, created, **kwargs):
    """
    Handle document upload events
    """
    if created:
        logger.info(
            f"Document uploaded: {instance.document_type} "
            f"for verification {instance.verification_id}, "
            f"size: {instance.file_size} bytes"
        )
        
        # Log document upload
        log_compliance_action(
            instance.user_id,
            "Document Uploaded",
            "upload",
            "document",
            str(instance.id),
            new_value={
                "type": instance.document_type,
                "file_name": instance.original_file_name,
                "size": instance.file_size
            }
        )


@receiver(pre_save, sender=KYCDocument)
def validate_document_status(sender, instance, **kwargs):
    """
    Validate document status changes
    """
    if instance.pk:
        try:
            old_doc = KYCDocument.objects.get(pk=instance.pk)
            
            # If status changed to approved, set verified_at
            if (old_doc.status != instance.status and 
                instance.status == VerificationStatus.APPROVED and 
                not instance.verified_at):
                instance.verified_at = timezone.now()
            
            # If status changed from approved, clear verified_at
            if (old_doc.status == VerificationStatus.APPROVED and 
                instance.status != VerificationStatus.APPROVED):
                instance.verified_at = None
                instance.verified_by = None
        
        except KYCDocument.DoesNotExist:
            pass


@receiver(post_save, sender=TACCode)
def handle_tac_code_creation(sender, instance, created, **kwargs):
    """
    Handle TAC code creation events
    """
    if created:
        logger.info(f"TAC code generated for user {instance.user_id}")
        
        # Log TAC generation
        log_compliance_action(
            instance.user_id,
            "TAC Code Generated",
            "generation",
            "tac",
            str(instance.id),
            new_value={
                "code_type": instance.code_type,
                "expires_at": instance.expires_at.isoformat()
            },
            ip_address=instance.ip_address
        )


@receiver(pre_save, sender=TACCode)
def validate_tac_code(sender, instance, **kwargs):
    """
    Validate TAC code before saving
    """
    if instance.is_used and not instance.used_at:
        instance.used_at = timezone.now()
    
    # Auto-expire if past expiry date
    if not instance.is_expired and instance.expires_at < timezone.now():
        instance.is_expired = True


@receiver(post_save, sender=WithdrawalRequest)
def handle_withdrawal_request(sender, instance, created, **kwargs):
    """
    Handle withdrawal request events
    """
    if created:
        logger.info(
            f"Withdrawal request created: {instance.id} "
            f"for user {instance.user_id}, amount: {instance.amount} {instance.currency}"
        )
        
        # Log withdrawal creation
        log_compliance_action(
            instance.user_id,
            "Withdrawal Request Created",
            "creation",
            "withdrawal",
            str(instance.id),
            new_value={
                "amount": instance.amount,
                "currency": instance.currency,
                "status": instance.status
            }
        )
    
    else:
        # Withdrawal updated - FIXED HERE
        update_fields = kwargs.get('update_fields', None)
        
        if update_fields and 'status' in update_fields:
            # Status changed
            logger.info(f"Withdrawal {instance.id} status changed to {instance.status}")
            
            # Log status change
            log_compliance_action(
                instance.user_id,
                "Withdrawal Status Changed",
                "status_change",
                "withdrawal",
                str(instance.id),
                new_value={"status": instance.status}
            )
            
            if instance.status == 'completed' and instance.processed_by:
                # Log completion by processor
                log_compliance_action(
                    instance.processed_by,
                    "Withdrawal Processed",
                    "processing",
                    "withdrawal",
                    str(instance.id),
                    entity_type="withdrawal",
                    new_value={
                        "processed_by": instance.processed_by,
                        "transaction_hash": instance.transaction_hash
                    }
                )


@receiver(post_save, sender=ComplianceCheck)
def handle_compliance_check(sender, instance, created, **kwargs):
    """
    Handle compliance check events
    """
    if created:
        logger.info(
            f"Compliance check performed: {instance.check_type} "
            f"for verification {instance.verification_id}, "
            f"risk score: {instance.risk_score}"
        )


@receiver(post_save, sender=ComplianceAuditLog)
def handle_audit_log(sender, instance, created, **kwargs):
    """
    Handle audit log events (meta-logging)
    """
    if created:
        # Don't create infinite loop by logging audit log creation
        pass


@receiver(post_save, sender=User)
def create_user_compliance_record(sender, instance, created, **kwargs):
    """
    Create initial compliance record for new users
    """
    if created:
        logger.info(f"New user created: {instance.id}, checking compliance requirements")
        
        # Note: We don't create KYC verification automatically
        # User must initiate KYC process themselves


@receiver(pre_delete, sender=KYCDocument)
def handle_document_deletion(sender, instance, **kwargs):
    """
    Handle document deletion
    """
    logger.info(f"Document deleted: {instance.id} for user {instance.user_id}")
    
    # Log deletion
    log_compliance_action(
        instance.user_id,
        "Document Deleted",
        "deletion",
        "document",
        str(instance.id),
        old_value={
            "type": instance.document_type,
            "file_name": instance.original_file_name
        }
    )
    
    # Note: File deletion from storage should be handled separately
    # Consider implementing a cleanup task for actual file deletion


@receiver(pre_delete, sender=KYCVerification)
def handle_verification_deletion(sender, instance, **kwargs):
    """
    Handle KYC verification deletion
    """
    logger.warning(f"KYC verification deleted: {instance.id} for user {instance.user_id}")
    
    # Log deletion (this won't be saved if cascade delete removes audit logs)
    # Consider implementing soft delete instead


# Scheduled task signals (would be connected to celery/cron)
def scheduled_compliance_tasks():
    """
    Function to run scheduled compliance tasks
    """
    try:
        # Clean up expired TAC codes
        expired_count = cleanup_expired_tac_codes()
        logger.info(f"Scheduled task: Cleaned up {expired_count} expired TAC codes")
        
        # Check for expired documents
        expired_docs = KYCDocument.objects.filter(
            verified_at__lt=timezone.now() - timezone.timedelta(days=365),
            status=VerificationStatus.APPROVED
        )
        
        for doc in expired_docs:
            doc.status = VerificationStatus.EXPIRED
            doc.save()
            logger.info(f"Marked document {doc.id} as expired")
        
        logger.info(f"Scheduled task: Checked {expired_docs.count()} documents for expiry")
        
    except Exception as e:
        logger.error(f"Error in scheduled compliance tasks: {e}")


# Connect signals for User model
try:
    from django.contrib.auth.models import User
    post_save.connect(create_user_compliance_record, sender=User)
except ImportError:
    pass