"""
Utility functions for notifications system
"""
from django.contrib.auth.models import User
from .models import Notification, NotificationTemplate, NotificationPreference


def create_notification(user, notification_type, title, message, **kwargs):
    """
    Helper function to create a notification
    
    Args:
        user: User object
        notification_type: Type of notification
        title: Notification title
        message: Notification message
        **kwargs: Additional fields (priority, action_url, etc.)
    
    Returns:
        Notification object
    """
    return Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        **kwargs
    )


def create_notification_from_template(user, template_type, context):
    """
    Create a notification using a template
    
    Args:
        user: User object
        template_type: Template type identifier
        context: Dictionary with template variables
    
    Returns:
        Notification object or None if template not found
    """
    try:
        template = NotificationTemplate.objects.get(
            template_type=template_type,
            is_active=True
        )
        rendered = template.render(context)
        
        return Notification.objects.create(
            user=user,
            notification_type=rendered['notification_type'],
            title=rendered['title'],
            message=rendered['message'],
            priority=rendered['priority'],
            action_url=rendered.get('action_url', ''),
            action_label=rendered.get('action_label', ''),
        )
    except NotificationTemplate.DoesNotExist:
        return None
    except KeyError as e:
        print(f"Missing template variable: {e}")
        return None


def send_transaction_notification(user, transaction):
    """
    Send notification for a transaction
    
    Args:
        user: User object
        transaction: Transaction object
    """
    from payments.models import Transaction
    
    transaction_type = transaction.transaction_type
    amount = f"${transaction.amount:,.2f}"
    
    if transaction.status == 'completed':
        if transaction_type in ['deposit', 'credit']:
            title = "Money Received"
            message = f"You received {amount} {transaction.currency}"
            notification_type = "payment"
        elif transaction_type in ['withdrawal', 'transfer']:
            title = "Money Sent"
            message = f"You sent {amount} {transaction.currency}"
            notification_type = "transfer"
        else:
            title = "Transaction Completed"
            message = f"Your {transaction_type} of {amount} was successful"
            notification_type = "transaction"
    elif transaction.status == 'failed':
        title = "Transaction Failed"
        message = f"Your {transaction_type} of {amount} failed"
        notification_type = "transaction"
    else:
        title = "Transaction Pending"
        message = f"Your {transaction_type} of {amount} is being processed"
        notification_type = "transaction"
    
    return create_notification(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        priority='high' if transaction.status == 'failed' else 'medium',
        action_url=f"/transactions/{transaction.transaction_id}",
        action_label="View Transaction",
        related_transaction_id=transaction.transaction_id,
        metadata={
            'transaction_type': transaction_type,
            'amount': float(transaction.amount),
            'currency': transaction.currency,
            'status': transaction.status
        }
    )


def send_security_alert(user, alert_type, details):
    """
    Send security notification
    
    Args:
        user: User object
        alert_type: Type of security alert
        details: Additional details
    """
    alerts = {
        'login_new_device': {
            'title': 'New Device Login',
            'message': f"Your account was accessed from a new device: {details.get('device', 'Unknown')}"
        },
        'password_changed': {
            'title': 'Password Changed',
            'message': 'Your password was successfully changed'
        },
        'failed_login': {
            'title': 'Failed Login Attempt',
            'message': f"Someone tried to access your account from {details.get('location', 'Unknown location')}"
        },
        'account_locked': {
            'title': 'Account Locked',
            'message': 'Your account has been temporarily locked due to suspicious activity'
        }
    }
    
    alert = alerts.get(alert_type, {
        'title': 'Security Alert',
        'message': 'There was a security event on your account'
    })
    
    return create_notification(
        user=user,
        notification_type='security',
        title=alert['title'],
        message=alert['message'],
        priority='urgent',
        action_url='/settings/security',
        action_label='View Security Settings',
        metadata=details
    )


def send_card_notification(user, card, action):
    """
    Send card-related notification
    
    Args:
        user: User object
        card: Card object
        action: Type of action (issued, blocked, transaction, etc.)
    """
    actions = {
        'issued': {
            'title': 'New Card Issued',
            'message': f"Your new {card.card_type} card ending in {card.card_number[-4:]} is ready"
        },
        'blocked': {
            'title': 'Card Blocked',
            'message': f"Your card ending in {card.card_number[-4:]} has been blocked"
        },
        'activated': {
            'title': 'Card Activated',
            'message': f"Your card ending in {card.card_number[-4:]} is now active"
        },
        'expired': {
            'title': 'Card Expiring Soon',
            'message': f"Your card ending in {card.card_number[-4:]} expires soon"
        }
    }
    
    notification = actions.get(action, {
        'title': 'Card Update',
        'message': f"There was an update to your card ending in {card.card_number[-4:]}"
    })
    
    return create_notification(
        user=user,
        notification_type='card',
        title=notification['title'],
        message=notification['message'],
        priority='high' if action == 'blocked' else 'medium',
        action_url='/cards',
        action_label='Manage Cards'
    )


def send_kyc_notification(user, status, details=None):
    """
    Send KYC verification notification
    
    Args:
        user: User object
        status: KYC status (approved, rejected, pending)
        details: Additional details
    """
    if status == 'approved':
        title = 'Verification Approved'
        message = 'Your identity verification was successful. Full account access is now enabled.'
        priority = 'high'
    elif status == 'rejected':
        title = 'Verification Declined'
        message = 'Your identity verification was unsuccessful. Please check the details and try again.'
        priority = 'urgent'
    else:
        title = 'Verification In Progress'
        message = 'Your identity verification is being reviewed. This usually takes 1-2 business days.'
        priority = 'medium'
    
    return create_notification(
        user=user,
        notification_type='kyc',
        title=title,
        message=message,
        priority=priority,
        action_url='/settings/verification',
        action_label='View Status',
        metadata=details or {}
    )


def send_savings_goal_notification(user, goal, event_type):
    """
    Send savings goal notification
    
    Args:
        user: User object
        goal: SavingsGoal object
        event_type: Type of event (reached, milestone, reminder)
    """
    if event_type == 'reached':
        title = 'Savings Goal Reached! 🎉'
        message = f"Congratulations! You've reached your goal: {goal.name}"
        priority = 'high'
    elif event_type == 'milestone':
        progress = (goal.current_amount / goal.target_amount) * 100
        title = 'Savings Milestone'
        message = f"You're {progress:.0f}% of the way to your goal: {goal.name}"
        priority = 'medium'
    else:
        title = 'Savings Reminder'
        message = f"Don't forget to contribute to your goal: {goal.name}"
        priority = 'low'
    
    return create_notification(
        user=user,
        notification_type='savings',
        title=title,
        message=message,
        priority=priority,
        action_url='/savings',
        action_label='View Goals'
    )


def send_subscription_reminder(user, subscription):
    """
    Send subscription reminder notification
    
    Args:
        user: User object
        subscription: Subscription object
    """
    from datetime import date
    
    days_until = (subscription.next_billing_date - date.today()).days
    
    if days_until <= 1:
        title = 'Subscription Due Tomorrow'
        priority = 'high'
    elif days_until <= 7:
        title = 'Upcoming Subscription Payment'
        priority = 'medium'
    else:
        return None  # Don't send if more than 7 days away
    
    message = f"{subscription.service_name} will charge ${subscription.amount} {subscription.currency} in {days_until} day{'s' if days_until != 1 else ''}"
    
    return create_notification(
        user=user,
        notification_type='subscription',
        title=title,
        message=message,
        priority=priority,
        action_url='/subscriptions',
        action_label='Manage Subscriptions'
    )


def send_promotional_notification(user, title, message, action_url=None):
    """
    Send promotional notification
    
    Args:
        user: User object
        title: Notification title
        message: Notification message
        action_url: Optional action URL
    """
    # Check if user has promotional notifications enabled
    try:
        prefs = user.notification_preferences
        if not prefs.promotional_notifications:
            return None
    except NotificationPreference.DoesNotExist:
        pass
    
    return create_notification(
        user=user,
        notification_type='promotion',
        title=title,
        message=message,
        priority='low',
        action_url=action_url or '',
        action_label='Learn More' if action_url else ''
    )


def bulk_send_notification(user_ids, notification_type, title, message, **kwargs):
    """
    Send notification to multiple users
    
    Args:
        user_ids: List of user IDs
        notification_type: Type of notification
        title: Notification title
        message: Notification message
        **kwargs: Additional fields
    
    Returns:
        List of created notifications
    """
    users = User.objects.filter(id__in=user_ids)
    notifications = []
    
    for user in users:
        notification = Notification(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            **kwargs
        )
        notifications.append(notification)
    
    return Notification.objects.bulk_create(notifications)


def cleanup_old_notifications(days=30):
    """
    Archive old read notifications
    
    Args:
        days: Number of days to keep notifications
    
    Returns:
        Number of archived notifications
    """
    from django.utils import timezone
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=days)
    
    count = Notification.objects.filter(
        is_read=True,
        is_archived=False,
        created_at__lt=cutoff_date
    ).update(is_archived=True)
    
    return count
