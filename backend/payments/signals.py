# payments/signals.py - ENHANCED VERSION
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.db import transaction
from decimal import Decimal
import logging
from .models import Account, Transaction, AuditLog

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_account(sender, instance, created, **kwargs):
    """Create a default account for new users"""
    if created:
        try:
            # Use transaction.atomic to ensure both accounts are created together
            with transaction.atomic():
                # Create checking account
                checking_account = Account.objects.create(
                    user=instance,
                    account_type='checking',
                    currency='USD',
                    balance=Decimal('0.00')
                )
                
                # Optionally create a savings account too
                savings_account = Account.objects.create(
                    user=instance,
                    account_type='savings',
                    currency='USD',
                    balance=Decimal('0.00')
                )
                
                # Log the account creation
                AuditLog.objects.create(
                    user=instance,
                    action='account_created',
                    details={
                        'checking_account_number': checking_account.account_number,
                        'savings_account_number': savings_account.account_number,
                        'user_id': instance.id,
                        'user_email': instance.email
                    }
                )
                
        except Exception as e:
            # Use logging instead of print for better error handling
            logger.error(f"Error creating accounts for user {instance.email}: {str(e)}")
            # Don't raise the exception to avoid breaking user creation


@receiver(post_save, sender=Account)
def log_account_changes(sender, instance, created, **kwargs):
    """Log account creation and updates"""
    # Avoid recursion from AuditLog saves
    if sender == AuditLog:
        return
    
    action = 'account_created' if created else 'account_updated'
    
    try:
        AuditLog.objects.create(
            user=instance.user,
            action=action,
            details={
                'account_id': instance.id,
                'account_number': instance.account_number,
                'account_type': instance.account_type,
                'balance': str(instance.balance),
                'currency': instance.currency,
                'is_active': instance.is_active
            }
        )
    except Exception as e:
        logger.error(f"Error creating audit log for account {instance.account_number}: {str(e)}")


@receiver(pre_save, sender=Transaction)
def validate_transaction_amount(sender, instance, **kwargs):
    """Validate transaction amount before saving"""
    if instance.amount <= Decimal('0.00'):
        raise ValueError("Transaction amount must be greater than 0")
    
    # Additional validation for transfer transactions
    if instance.transaction_type == 'transfer':
        if not instance.from_account:
            raise ValueError("Transfer transaction requires a from_account")
        if not instance.to_account:
            raise ValueError("Transfer transaction requires a to_account")
        if instance.from_account == instance.to_account:
            raise ValueError("Cannot transfer to the same account")
        if instance.from_account.balance < instance.amount:
            raise ValueError("Insufficient funds")


@receiver(post_save, sender=Transaction)
def log_transaction_creation(sender, instance, created, **kwargs):
    """Log transaction creation"""
    # Avoid recursion from AuditLog saves
    if sender == AuditLog:
        return
    
    if created:
        try:
            audit_details = {
                'transaction_id': instance.transaction_id,
                'transaction_type': instance.transaction_type,
                'amount': str(instance.amount),
                'currency': instance.currency,
                'status': instance.status
            }
            
            # Add account information based on transaction type
            if instance.transaction_type == 'transfer':
                if instance.from_account:
                    audit_details['from_account'] = instance.from_account.account_number
                if instance.to_account:
                    audit_details['to_account'] = instance.to_account.account_number
            elif instance.account:
                audit_details['account'] = instance.account.account_number
            
            # Determine which user to associate with the audit log
            user = None
            if instance.from_account:
                user = instance.from_account.user
            elif instance.account:
                user = instance.account.user
            
            # If it's a transfer between different users, we might want to log for both
            # For simplicity, we'll log for the initiating user
            if user:
                AuditLog.objects.create(
                    user=user,
                    action='transaction_created',
                    details=audit_details
                )
                
        except Exception as e:
            logger.error(f"Error creating transaction audit log: {str(e)}")


@receiver(post_save, sender=Transaction)
def update_account_status_after_failed_transaction(sender, instance, **kwargs):
    """Deactivate account after multiple failed transactions"""
    # Avoid recursion from AuditLog saves
    if sender == AuditLog:
        return
    
    if instance.status == 'failed':
        try:
            # Determine which account to check
            account_to_check = None
            if instance.account:
                account_to_check = instance.account
            elif instance.from_account:
                account_to_check = instance.from_account
            
            if account_to_check:
                # Check if account has multiple failed transactions
                failed_count = Transaction.objects.filter(
                    account=account_to_check,
                    status='failed'
                ).count()
                
                if failed_count >= 3:  # After 3 failed transactions
                    account_to_check.is_active = False
                    account_to_check.save()
                    
                    AuditLog.objects.create(
                        user=account_to_check.user,
                        action='account_deactivated',
                        details={
                            'account_number': account_to_check.account_number,
                            'reason': 'multiple_failed_transactions',
                            'failed_count': failed_count
                        }
                    )
                    
        except Exception as e:
            logger.error(f"Error updating account status: {str(e)}")


@receiver(post_delete, sender=User)
def log_user_deletion(sender, instance, **kwargs):
    """Log when a user is deleted"""
    try:
        AuditLog.objects.create(
            user=None,  # System action
            action='user_deleted',
            details={
                'user_id': instance.id,
                'user_email': instance.email,
                'deleted_at': 'immediate'  # Simplified since we don't have _deleted_at field
            }
        )
    except Exception as e:
        logger.error(f"Error logging user deletion: {str(e)}")