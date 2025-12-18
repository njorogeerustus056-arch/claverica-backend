from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserTask, UserRewardBalance, RewardWithdrawal
from django.utils import timezone

# -----------------------
# Update UserRewardBalance when UserTask is created
# -----------------------
@receiver(post_save, sender=UserTask)
def update_balance_on_task_create(sender, instance, created, **kwargs):
    if created:
        balance, _ = UserRewardBalance.objects.get_or_create(user=instance.user)
        balance.tasks_pending += 1
        balance.pending_balance += instance.task.reward_amount
        balance.save()

# -----------------------
# Update UserRewardBalance when UserTask is completed
# -----------------------
@receiver(post_save, sender=UserTask)
def update_balance_on_task_completed(sender, instance, **kwargs):
    if instance.status == 'completed':
        balance, _ = UserRewardBalance.objects.get_or_create(user=instance.user)
        if instance.reward_earned > 0:
            balance.add_earnings(instance.reward_earned)
            # Reduce pending balance if it was counted
            balance.pending_balance -= instance.reward_earned
            if balance.pending_balance < 0:
                balance.pending_balance = 0
            balance.save()

# -----------------------
# Deduct available balance when a withdrawal is created
# -----------------------
@receiver(post_save, sender=RewardWithdrawal)
def deduct_balance_on_withdrawal(sender, instance, created, **kwargs):
    if created:
        balance, _ = UserRewardBalance.objects.get_or_create(user=instance.user)
        balance.deduct_withdrawal(instance.amount)

