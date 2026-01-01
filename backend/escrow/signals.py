from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Escrow, EscrowLog

@receiver(post_save, sender=Escrow)
def create_escrow_log(sender, instance, created, **kwargs):
    """
    Automatically create a log entry when escrow is created
    """
    if created:
        EscrowLog.objects.create(
            escrow=instance,
            user_id=instance.sender_id,
            user_name=instance.sender_name,
            action='created',
            details=f"Auto-created log for escrow {instance.escrow_id}"
        )