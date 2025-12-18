"""
Utility functions for the notifications system
"""
from typing import Optional, Dict, Any, List
from django.contrib.auth.models import User
from .models import Notification, NotificationTemplate, NotificationPreference


def create_notification(
    user: User,
    notification_type: str,
    title: str,
    message: str,
    **kwargs
) -> Notification:
    """
    Helper function to create a notification.
    """
    return Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        **kwargs
    )


def create_notification_from_template(
    user: User,
    template_type: str,
    context: Dict[str, Any]
) -> Optional[Notification]:
    """
    Create a notification using a template.
    """
    try:
        template = NotificationTemplate.objects.get(template_type=template_type, is_active=True)
        rendered = template.render(context)

        return Notification.objects.create(
            user=user,
            notification_type=rendered['notification_type'],
            title=rendered['title'],
            message=rendered['message'],
            priority=rendered.get('priority', 'medium'),
            action_url=rendered.get('action_url', ''),
            action_label=rendered.get('action_label', ''),
        )
    except NotificationTemplate.DoesNotExist:
        return None
    except KeyError as e:
        print(f"[Notification Utils] Missing template variable: {e}")
        return None


def send_transaction_notification(user: User, transaction) -> Notification:
    """
    Send notification for a transaction.
    """
    transaction_type = transaction.transaction_type
    amount = f"${transaction.amount:,.2f}"

    if transaction.status == 'completed':
        if transaction_type in ['deposit', 'credit']:
            title, message, n_type = "Money Received", f"You received {amount} {transaction.currency}", "payment"
        elif transaction_type in ['withdrawal', 'transfer']:
            title, message, n_type = "Money Sent", f"You sent {amount} {transaction.currency}", "transfer"
        else:
            title, message, n_type = "Transaction Completed", f"Your {transaction_type} of {amount} was successful", "transaction"
    elif transaction.status == 'failed':
        title, message, n_type = "Transaction Failed", f"Your {transaction_type} of {amount} failed", "transaction"
    else:
        title, message, n_type = "Transaction Pending", f"Your {transaction_type} of {amount} is being processed", "transaction"

    return create_notification(
        user=user,
        notification_type=n_type,
        title=title,
        message=message,
        priority='high' if transaction.status == 'failed' else 'medium',
        action_url=f"/transactions/{transaction.transaction_id}",
        action_label="View Transaction",
        related_transaction_id=getattr(transaction, 'transaction_id', None),
        metadata={
            'transaction_type': transaction_type,
            'amount': float(transaction.amount),
            'currency': transaction.currency,
            'status': transaction.status
        }
    )


def send_security_alert(user: User, alert_type: str, details: Optional[Dict[str, Any]] = None) -> Notification:
    """
    Send security-related notification.
    """
    alerts = {
        'login_new_device': {
            'title': 'New Device Login',
            'message': f"Your account was accessed from a new device: {details.get('device', 'Unknown') if details else 'Unknown'}"
        },
        'password_changed': {
            'title': 'Password Changed',
            'message': 'Your password was successfully changed'
        },
        'failed_login': {
            'title': 'Failed Login Attempt',
            'message': f"Someone tried to access your account from {details.get('location', 'Unknown location') if details else 'Unknown location'}"
        },
        'account_locked': {
            'title': 'Account Locked',
            'message': 'Your account has been temporarily locked due to suspicious activity'
        }
    }

    alert = alerts.get(alert_type, {'title': 'Security Alert', 'message': 'There was a security event on your account'})

    return create_notification(
        user=user,
        notification_type='security',
        title=alert['title'],
        message=alert['message'],
        priority='urgent',
        action_url='/settings/security',
        action_label='View Security Settings',
        metadata=details or {}
    )


def send_card_notification(user: User, card, action: str) -> Notification:
    """
    Send card-related notification.
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


def send_kyc_notification(user: User, status: str, details: Optional[Dict[str, Any]] = None) -> Notification:
    """
    Send KYC verification notification.
    """
    status_map = {
        'approved': ('Verification Approved', 'Your identity verification was successful. Full account access is now enabled.', 'high'),
        'rejected': ('Verification Declined', 'Your identity verification was unsuccessful. Please check the details and try again.', 'urgent'),
        'pending': ('Verification In Progress', 'Your identity verification is being reviewed. This usually takes 1-2 business days.', 'medium')
    }

    title, message, priority = status_map.get(status, ('Verification Update', 'Your verification status has been updated.', 'medium'))

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


def send_savings_goal_notification(user: User, goal, event_type: str) -> Notification:
    """
    Send savings goal notifications.
    """
    if event_type == 'reached':
        title, message, priority = 'Savings Goal Reached! 🎉', f"Congratulations! You've reached your goal: {goal.name}", 'high'
    elif event_type == 'milestone':
        progress = (goal.current_amount / goal.target_amount) * 100
        title, message, priority = 'Savings Milestone', f"You're {progress:.0f}% of the way to your goal: {goal.name}", 'medium'
    else:
        title, message, priority = 'Savings Reminder', f"Don't forget to contribute to your goal: {goal.name}", 'low'

    return create_notification(
        user=user,
        notification_type='savings',
        title=title,
        message=message,
        priority=priority,
        action_url='/savings',
        action_label='View Goals'
    )


def send_subscription_reminder(user: User, subscription) -> Optional[Notification]:
    """
    Send subscription reminder notification.
    """
    from datetime import date

    days_until = (subscription.next_billing_date - date.today()).days

    if days_until > 7:
        return None

    title = 'Subscription Due Tomorrow' if days_until <= 1 else 'Upcoming Subscription Payment'
    priority = 'high' if days_until <= 1 else 'medium'

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


def send_promotional_notification(user: User, title: str, message: str, action_url: Optional[str] = None) -> Optional[Notification]:
    """
    Send promotional notification if user opted in.
    """
    try:
        prefs: NotificationPreference = user.notification_preferences
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


def bulk_send_notification(user_ids: List[int], notification_type: str, title: str, message: str, **kwargs) -> List[Notification]:
    """
    Send notifications to multiple users.
    """
    users = User.objects.filter(id__in=user_ids)
    notifications = [Notification(user=user, notification_type=notification_type, title=title, message=message, **kwargs) for user in users]
    return Notification.objects.bulk_create(notifications)


def cleanup_old_notifications(days: int = 30) -> int:
    """
    Archive read notifications older than a certain number of days.
    """
    from django.utils import timezone
    from datetime import timedelta

    cutoff_date = timezone.now() - timedelta(days=days)
    return Notification.objects.filter(is_read=True, is_archived=False, created_at__lt=cutoff_date).update(is_archived=True)
