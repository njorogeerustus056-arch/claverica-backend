"""
transfers/signals.py - Signals for transfer compliance integration
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Transfer, TransferLog
from .services import TransferComplianceService


@receiver(pre_save, sender=Transfer)
def track_transfer_status_change(sender, instance, **kwargs):
    """Track transfer status changes for audit trail"""
    if instance.pk:
        try:
            old_instance = Transfer.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
            instance._old_risk_level = old_instance.risk_level
        except Transfer.DoesNotExist:
            instance._old_status = None
            instance._old_risk_level = None


@receiver(post_save, sender=Transfer)
def handle_transfer_status_change(sender, instance, created, **kwargs):
    """Handle transfer status changes and compliance integration"""
    if created:
        # New transfer created
        TransferLog.objects.create(
            transfer=instance,
            log_type='created',
            message='Transfer created',
            metadata={'amount': str(instance.amount), 'currency': instance.currency}
        )
        
        # Create compliance request if not in draft
        if instance.status != 'draft':
            try:
                TransferComplianceService.create_compliance_request(instance)
            except Exception as e:
                TransferLog.objects.create(
                    transfer=instance,
                    log_type='compliance_check',
                    message=f'Failed to create compliance request: {str(e)}',
                    metadata={'error': str(e)}
                )
    
    elif hasattr(instance, '_old_status') and instance._old_status != instance.status:
        # Status changed
        TransferLog.objects.create(
            transfer=instance,
            log_type='status_change',
            message=f'Status changed from {instance._old_status} to {instance.status}',
            metadata={
                'old_status': instance._old_status,
                'new_status': instance.status
            }
        )
        
        # Update compliance request status if exists
        if instance.compliance_request:
            status_map = {
                'pending': 'pending',
                'processing': 'under_review',
                'completed': 'approved',
                'cancelled': 'rejected',
                'failed': 'rejected',
                'compliance_review': 'under_review',
                'awaiting_tac': 'awaiting_tac',
                'awaiting_video_call': 'awaiting_video_call',
            }
            
            compliance_status = status_map.get(instance.status)
            if compliance_status and instance.compliance_request.status != compliance_status:
                instance.compliance_request.status = compliance_status
                instance.compliance_request.save()
    
    # Handle risk level changes
    if (hasattr(instance, '_old_risk_level') and 
        instance._old_risk_level != instance.risk_level):
        
        TransferLog.objects.create(
            transfer=instance,
            log_type='risk_change',
            message=f'Risk level changed from {instance._old_risk_level} to {instance.risk_level}',
            metadata={
                'old_risk_level': instance._old_risk_level,
                'new_risk_level': instance.risk_level
            }
        )
        
        # Flag for review if risk becomes high
        if instance.risk_level == 'high' and instance.status == 'pending':
            instance.status = 'compliance_review'
            instance.save()


@receiver(post_save, sender=ComplianceProfile)
def handle_compliance_profile_change(sender, instance, created, **kwargs):
    """Handle compliance profile changes for user's pending transfers"""
    if not created and hasattr(instance, '_old_kyc_status'):
        # KYC status changed
        if instance._old_kyc_status != instance.kyc_status:
            
            if instance.kyc_status == 'rejected':
                # Cancel all pending transfers for user
                pending_transfers = Transfer.objects.filter(
                    user=instance.user,
                    status__in=['pending', 'awaiting_tac', 'awaiting_video_call', 'compliance_review']
                )
                
                for transfer in pending_transfers:
                    transfer.status = 'cancelled'
                    transfer.save()
                    
                    TransferLog.objects.create(
                        transfer=transfer,
                        log_type='status_change',
                        message=f'Transfer cancelled due to KYC rejection',
                        metadata={
                            'kyc_old_status': instance._old_kyc_status, 
                            'kyc_new_status': instance.kyc_status
                        }
                    )
            
            elif instance.kyc_status == 'approved':
                # Re-assess pending transfers
                pending_transfers = Transfer.objects.filter(
                    user=instance.user,
                    status__in=['pending', 'compliance_review']
                )
                
                for transfer in pending_transfers:
                    try:
                        TransferComplianceService.assess_transfer_risk(transfer)
                    except Exception as e:
                        TransferLog.objects.create(
                            transfer=transfer,
                            log_type='compliance_check',
                            message=f'Failed to re-assess transfer after KYC approval: {str(e)}',
                            metadata={'error': str(e)}
                        )
        
        # Risk level changed
        if hasattr(instance, '_old_risk_level') and instance._old_risk_level != instance.risk_level:
            if instance.risk_level == 'high':
                # Flag all pending transfers for review
                pending_transfers = Transfer.objects.filter(
                    user=instance.user,
                    status__in=['pending', 'awaiting_tac', 'awaiting_video_call']
                )
                
                for transfer in pending_transfers:
                    transfer.status = 'compliance_review'
                    transfer.save()
                    
                    TransferLog.objects.create(
                        transfer=transfer,
                        log_type='status_change',
                        message=f'Transfer flagged for compliance review due to increased risk level',
                        metadata={
                            'old_risk_level': instance._old_risk_level, 
                            'new_risk_level': instance.risk_level
                        }
                    )
                    
                    # Create compliance alert
                    try:
                        ComplianceAlert.objects.create(
                            user=instance.user,
                            alert_type='risk_level_change',
                            title=f'Transfer flagged due to risk level change',
                            description=f'User risk level changed from {instance._old_risk_level} to {instance.risk_level}. Transfer {transfer.transfer_id} requires review.',
                            severity='medium',
                            metadata={
                                'transfer_id': transfer.transfer_id,
                                'old_risk_level': instance._old_risk_level,
                                'new_risk_level': instance.risk_level,
                                'amount': str(transfer.amount),
                                'currency': transfer.currency
                            }
                        )
                    except Exception as e:
                        TransferLog.objects.create(
                            transfer=transfer,
                            log_type='alert',
                            message=f'Failed to create compliance alert: {str(e)}',
                            metadata={'error': str(e)}
                        )


@receiver(pre_save, sender=ComplianceProfile)
def track_compliance_profile_changes(sender, instance, **kwargs):
    """Track compliance profile changes"""
    if instance.pk:
        try:
            old_instance = ComplianceProfile.objects.get(pk=instance.pk)
            instance._old_kyc_status = old_instance.kyc_status
            instance._old_risk_level = old_instance.risk_level
        except ComplianceProfile.DoesNotExist:
            instance._old_kyc_status = None
            instance._old_risk_level = None