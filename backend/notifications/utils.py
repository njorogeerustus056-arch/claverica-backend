"""
Utility functions for the notifications system
"""
from typing import Optional, Dict, Any, List
from django.contrib.auth.models import User
from .models import Notification, NotificationTemplate
from .pusher_client import trigger_notification


def create_notification(
    user: User,
    notification_type: str,
    title: str,
    message: str,
    **kwargs
) -> Notification:
    """
    Helper function to create a notification and trigger Pusher.
    """
    notification = Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        **kwargs
    )

    # Trigger real-time Pusher event via centralized client
    trigger_notification(
        user_id=user.id,
        event="new_notification",
        data={
            "id": notification.id,
            "notification_id": str(notification.notification_id),
            "title": notification.title,
            "message": notification.message,
            "notification_type": notification.notification_type,
            "priority": notification.priority,
            "metadata": notification.metadata or {},
            "created_at": notification.created_at.isoformat(),
            "is_read": notification.is_read,
            "action_url": notification.action_url or "",
            "action_label": notification.action_label or "",
            "time_ago": notification.time_ago
        }
    )

    return notification


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

        notification = Notification.objects.create(
            user=user,
            notification_type=rendered['notification_type'],
            title=rendered['title'],
            message=rendered['message'],
            priority=rendered.get('priority', 'medium'),
            action_url=rendered.get('action_url', ''),
            action_label=rendered.get('action_label', ''),
        )

        # Trigger Pusher event via centralized client
        trigger_notification(
            user_id=user.id,
            event="new_notification",
            data={
                "id": notification.id,
                "notification_id": str(notification.notification_id),
                "title": notification.title,
                "message": notification.message,
                "notification_type": notification.notification_type,
                "priority": notification.priority,
                "metadata": notification.metadata or {},
                "created_at": notification.created_at.isoformat(),
                "is_read": notification.is_read,
                "action_url": notification.action_url or "",
                "action_label": notification.action_label or "",
                "time_ago": notification.time_ago
            }
        )

        return notification
    except NotificationTemplate.DoesNotExist:
        return None
    except KeyError as e:
        print(f"[Notification Utils] Missing template variable: {e}")
        return None


def send_transaction_notification(user: User, transaction) -> Notification:
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