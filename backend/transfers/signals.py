"""
Transfer Signals - Automated actions for transfer events
"""

from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone

from .models import Transfer, TAC, TransferLog


@receiver(pre_save, sender=Transfer)
def track_transfer_changes(sender, instance, **kwargs):
    """Track transfer changes for audit trail"""
    if instance.pk:
        try:
            old_instance = Transfer.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except Transfer.DoesNotExist:
            instance._old_status = None


@receiver(post_save, sender=Transfer)
def handle_transfer_status_change(sender, instance, created, **kwargs):
    """Handle transfer status changes"""
    if created:
        # New transfer created
        TransferLog.objects.create(
            transfer=instance,
            log_type='created',
            message=f'Transfer request created for ${instance.amount} to {instance.recipient_name}'
        )

    elif hasattr(instance, '_old_status') and instance._old_status != instance.status:
        # Status changed
        TransferLog.objects.create(
            transfer=instance,
            log_type='status_change',
            message=f'Status changed from {instance._old_status} to {instance.status}'
        )


@receiver(pre_save, sender=TAC)
def track_tac_changes(sender, instance, **kwargs):
    """Track TAC changes"""
    if instance.pk:
        try:
            old_instance = TAC.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except TAC.DoesNotExist:
            instance._old_status = None


@receiver(post_save, sender=TAC)
def handle_tac_status_change(sender, instance, created, **kwargs):
    """Handle TAC status changes"""
    if created:
        # New TAC created
        TransferLog.objects.create(
            transfer=instance.transfer,
            log_type='tac_sent',
            message=f'TAC generated for transfer {instance.transfer.reference}'
        )

    elif hasattr(instance, '_old_status') and instance._old_status != instance.status:
        # TAC status changed
        TransferLog.objects.create(
            transfer=instance.transfer,
            log_type='tac_status_change',
            message=f'TAC status changed from {instance._old_status} to {instance.status}'
        )


@receiver(pre_delete, sender=Transfer)
def log_transfer_deletion(sender, instance, **kwargs):
    """Log transfer deletion"""
    TransferLog.objects.create(
        transfer=instance,
        log_type='deleted',
        message=f'Transfer {instance.reference} was deleted'
    )
