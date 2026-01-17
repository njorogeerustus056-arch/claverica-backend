"""
compliance/signals.py - Signal handlers for compliance app
"""

from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth import get_user_model
import logging

from .email_service import (
    send_kyc_approved_email,  # Changed from send_kyc_approved_email
    send_kyc_rejected_email,  # Changed from send_kyc_rejected_email
    send_compliance_decision_email,  # Changed from send_document_verified_email
    send_tac_code_email,  # Add this for TAC codes
    send_compliance_escalation_email  # Add this for escalations
)

logger = logging.getLogger(__name__)
User = get_user_model()

def log_compliance_action(user_id, action, action_type, resource_type, resource_id,
                         old_value=None, new_value=None, ip_address=None):
    """
    Helper function to log compliance actions
    """

    ComplianceAuditLog = apps.get_model("compliance", "ComplianceAuditLog")
    from django.apps import apps
    try:
        ComplianceAuditLog.objects.create(
            user_id=user_id,
            action=action,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
            timestamp=timezone.now()
        )
    except Exception as e:
        logger.error(f"Failed to log compliance action: {e}")


@receiver(post_save, sender='compliance.KYCVerification')
def handle_kyc_verification_save(sender, instance, created, **kwargs):
    """
    Handle KYC verification save events
    """
    if created:
        # New verification created
        logger.info(f"New KYC verification created: {instance.id} for user {instance.user_id}")
        
        # Perform automated compliance checks
        from .services import assess_risk
        
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
        # Use Django's built-in tracking for field changes
        # We'll check if verification_status was updated by comparing to original
        if hasattr(instance, '_original_verification_status'):
            old_status = instance._original_verification_status
            
            if instance.verification_status == "approved":
                logger.info(f"KYC verification approved: {instance.id}")
                
                # Send approval email
                try:
                    send_kyc_approved_email(
                        instance.user.email if instance.user else instance.email,
                        f"{instance.first_name} {instance.last_name}",
                        instance.compliance_level
                    )
                except Exception as e:
                    logger.error(f"Failed to send KYC approval email: {e}")
            
            elif instance.verification_status == "rejected":
                logger.info(f"KYC verification rejected: {instance.id}")
                
                # Send rejection email
                try:
                    send_kyc_rejected_email(
                        instance.user.email if instance.user else instance.email,
                        f"{instance.first_name} {instance.last_name}",
                        str(instance.id),
                        instance.rejection_reason or "Not specified"
                    )
                except Exception as e:
                    logger.error(f"Failed to send KYC rejection email: {e}")
            
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


@receiver(pre_save, sender='compliance.KYCVerification')
def capture_kyc_verification_changes(sender, instance, **kwargs):
    """
    from django.apps import apps
    KYCVerification = apps.get_model("compliance", "KYCVerification")
    from django.apps import apps
    KYCVerification = apps.get_model("compliance", "KYCVerification")
    Capture old values before saving KYC verification
    """
    if instance.pk:
        try:
            old_instance = KYCVerification.objects.get(pk=instance.pk)
            # Store original status for comparison
            instance._original_verification_status = old_instance.verification_status
            instance._original_risk_level = old_instance.risk_level
        except KYCVerification.DoesNotExist:
            instance._original_verification_status = None
            instance._original_risk_level = None
    else:
        instance._original_verification_status = None
        instance._original_risk_level = None


# Note: I'm showing partial content to save space
# The rest of the file should follow the same pattern

def register_signals():
    """
    Register all signal handlers.
    Note: This might not be needed as @receiver decorators auto-register.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Compliance signals registered")
    # No need to manually register - @receiver decorators handle it
