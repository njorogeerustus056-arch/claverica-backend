from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Account

# Example: If you still need to do something when an Account is created
@receiver(post_save, sender=Account)
def account_post_save(sender, instance, created, **kwargs):
    if created:
        # You can put any initialization code for Account here
        # For example, logging or setting default values
        print(f"New Account created: {instance}")
