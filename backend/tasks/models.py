# Tasks/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone
# REMOVED: import django.db.models as models  # DUPLICATE IMPORT - CAUSING CONFLICT

User = get_user_model()  # Works with custom user model (like your Account model)

# -------------------------
# Task Model
# -------------------------
class Task(models.Model):
    """Model for available tasks"""
    
    TASK_TYPES = (
        ('review', 'Product Review'),
        ('survey', 'Survey'),
        ('verification', 'Account Verification'),
        ('referral', 'Referral'),
        ('other', 'Other'),
    )
    
    TASK_STATUS = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    task_type = models.CharField(max_length=20, choices=TASK_TYPES, default='review')
    
    # Reward
    reward_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(max_length=10, default='USD')
    
    # Task Details
    estimated_time = models.IntegerField(help_text="Estimated time in minutes", default=5)
    max_completions = models.IntegerField(
        null=True,
        blank=True,
        help_text="Max number of users who can complete this task"
    )
    current_completions = models.IntegerField(default=0)
    
    # Requirements
    requires_verification = models.BooleanField(default=False)
    min_account_age_days = models.IntegerField(default=0)
    
    # Status
    status = models.CharField(max_length=20, choices=TASK_STATUS, default='active')
    
    # Instructions
    instructions = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        app_label = 'tasks'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'task_type']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.reward_amount} {self.currency}"
    
    def is_available(self):
        """Check if task is still available"""
        if self.status != 'active':
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        if self.max_completions and self.current_completions >= self.max_completions:
            return False
        return True


# -------------------------
# UserTask Model
# -------------------------
class UserTask(models.Model):
    """Model for tracking user task completions"""
    
    COMPLETION_STATUS = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    )
    
    # CHANGED: related_name='user_tasks' to 'tasks'
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='user_completions')
    
    # Status
    status = models.CharField(max_length=20, choices=COMPLETION_STATUS, default='pending')
    
    # Submission
    submission_data = models.JSONField(null=True, blank=True, help_text="Any data submitted by user")
    submission_notes = models.TextField(blank=True, null=True)
    
    # Reward
    reward_earned = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    reward_paid = models.BooleanField(default=False)
    reward_paid_at = models.DateTimeField(null=True, blank=True)
    
    # Review
    reviewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_tasks'
    )
    review_notes = models.TextField(blank=True, null=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        app_label = 'tasks'
        ordering = ['-started_at']
        unique_together = ['user', 'task']
        db_table = 'tasks_usertask'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['reward_paid']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.task.title} - {self.status}"
    
    def mark_completed(self):
        """Mark task as completed and award reward"""
        if self.status != 'completed':
            self.status = 'completed'
            self.completed_at = timezone.now()
            self.reward_earned = self.task.reward_amount
            self.save()
            # Increment task completion count
            self.task.current_completions += 1
            self.task.save()


# -------------------------
# TaskCategory Model
# -------------------------
class TaskCategory(models.Model):
    """Model for task categories"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, default="📋", help_text="Emoji or icon class")
    
    # Display
    color = models.CharField(max_length=50, default="blue")
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'tasks'
        ordering = ['display_order', 'name']
        verbose_name_plural = 'Task Categories'
    
    def __str__(self):
        return self.name


# -------------------------
# RewardWithdrawal Model
# -------------------------
class RewardWithdrawal(models.Model):
    """Model for reward withdrawals"""
    
    WITHDRAWAL_STATUS = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )
    
    WITHDRAWAL_METHODS = (
        ('bank', 'Bank Transfer'),
        ('paypal', 'PayPal'),
        ('crypto', 'Cryptocurrency'),
        ('internal', 'Internal Account'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reward_withdrawals')
    
    # Amount
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(max_length=10, default='USD')
    
    # Withdrawal Details
    withdrawal_method = models.CharField(max_length=20, choices=WITHDRAWAL_METHODS)
    account_details = models.JSONField(help_text="Bank account, PayPal email, crypto address, etc.")
    
    # Status
    status = models.CharField(max_length=20, choices=WITHDRAWAL_STATUS, default='pending')
    
    # Processing
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    processor_notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        app_label = 'tasks'
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.amount} {self.currency} - {self.status}"


# -------------------------
# UserRewardBalance Model
# -------------------------
class UserRewardBalance(models.Model):
    """Model for tracking user reward balances"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='reward_balance')
    
    # Balance
    total_earned = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_withdrawn = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    available_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    pending_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    currency = models.CharField(max_length=10, default='USD')
    
    # Stats
    tasks_completed = models.IntegerField(default=0)
    tasks_pending = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'tasks'
        verbose_name = 'User Reward Balance'
        verbose_name_plural = 'User Reward Balances'
    
    def __str__(self):
        return f"{self.user.email} - Balance: {self.available_balance} {self.currency}"
    
    def add_earnings(self, amount):
        """Add earnings to user balance"""
        self.total_earned += amount
        self.available_balance += amount
        self.tasks_completed += 1
        self.save()
    
    def deduct_withdrawal(self, amount):
        """Deduct withdrawal from available balance"""
        if self.available_balance >= amount:
            self.available_balance -= amount
            self.total_withdrawn += amount
            self.save()
            return True
        return False