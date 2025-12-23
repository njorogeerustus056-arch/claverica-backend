# notifications/management.py
"""
Management command to create or update default notification templates.

Run: python manage.py create_notification_templates
"""

from django.core.management.base import BaseCommand
from notifications.models import NotificationTemplate


class Command(BaseCommand):
    help = 'Create or update default notification templates'

    def handle(self, *args, **kwargs):
        templates = [
            {
                'template_type': 'transaction_success',
                'title_template': 'Transaction Successful',
                'message_template': 'Your {transaction_type} of ${amount} {currency} was completed successfully.',
                'notification_type': 'transaction',
                'priority': 'medium',
                'action_url_template': '/transactions/{transaction_id}',
                'action_label': 'View Transaction',
            },
            {
                'template_type': 'transaction_failed',
                'title_template': 'Transaction Failed',
                'message_template': 'Your {transaction_type} of ${amount} {currency} failed. {reason}',
                'notification_type': 'transaction',
                'priority': 'high',
                'action_url_template': '/transactions/{transaction_id}',
                'action_label': 'View Details',
            },
            {
                'template_type': 'login_new_device',
                'title_template': 'New Device Login',
                'message_template': 'Your account was accessed from {device} in {location}. If this wasn\'t you, secure your account immediately.',
                'notification_type': 'security',
                'priority': 'urgent',
                'action_url_template': '/settings/security',
                'action_label': 'Review Security',
            },
            {
                'template_type': 'password_changed',
                'title_template': 'Password Changed',
                'message_template': 'Your password was successfully changed on {date}. If you didn\'t make this change, contact support immediately.',
                'notification_type': 'security',
                'priority': 'high',
                'action_url_template': '/settings/security',
                'action_label': 'Security Settings',
            },
            {
                'template_type': 'card_issued',
                'title_template': 'New Card Issued',
                'message_template': 'Your new {card_type} card ending in {last_four} is ready to use.',
                'notification_type': 'card',
                'priority': 'medium',
                'action_url_template': '/cards',
                'action_label': 'View Card',
            },
            {
                'template_type': 'card_blocked',
                'title_template': 'Card Blocked',
                'message_template': 'Your card ending in {last_four} has been blocked for security reasons.',
                'notification_type': 'card',
                'priority': 'urgent',
                'action_url_template': '/cards',
                'action_label': 'Manage Cards',
            },
            {
                'template_type': 'payment_received',
                'title_template': 'Payment Received',
                'message_template': 'You received ${amount} {currency} from {sender}.',
                'notification_type': 'payment',
                'priority': 'medium',
                'action_url_template': '/transactions',
                'action_label': 'View Transaction',
            },
            {
                'template_type': 'transfer_completed',
                'title_template': 'Transfer Completed',
                'message_template': 'Your transfer of ${amount} {currency} to {recipient} was successful.',
                'notification_type': 'transfer',
                'priority': 'medium',
                'action_url_template': '/transactions',
                'action_label': 'View Details',
            },
            {
                'template_type': 'kyc_approved',
                'title_template': 'Verification Approved ✓',
                'message_template': 'Congratulations! Your identity verification was successful. You now have full access to all features.',
                'notification_type': 'kyc',
                'priority': 'high',
                'action_url_template': '/settings/verification',
                'action_label': 'View Status',
            },
            {
                'template_type': 'kyc_rejected',
                'title_template': 'Verification Declined',
                'message_template': 'Your identity verification was unsuccessful. Reason: {reason}. Please resubmit your documents.',
                'notification_type': 'kyc',
                'priority': 'urgent',
                'action_url_template': '/settings/verification',
                'action_label': 'Resubmit',
            },
            {
                'template_type': 'low_balance',
                'title_template': 'Low Balance Alert',
                'message_template': 'Your account balance is ${balance} {currency}. Consider adding funds to avoid overdraft fees.',
                'notification_type': 'account',
                'priority': 'medium',
                'action_url_template': '/accounts',
                'action_label': 'Add Funds',
            },
            {
                'template_type': 'savings_goal_reached',
                'title_template': 'Savings Goal Reached! 🎉',
                'message_template': 'Congratulations! You\'ve reached your savings goal "{goal_name}" of ${target_amount}!',
                'notification_type': 'savings',
                'priority': 'high',
                'action_url_template': '/savings',
                'action_label': 'View Goals',
            },
            {
                'template_type': 'subscription_reminder',
                'title_template': 'Upcoming Subscription Payment',
                'message_template': '{service_name} will charge ${amount} {currency} on {billing_date}.',
                'notification_type': 'subscription',
                'priority': 'medium',
                'action_url_template': '/subscriptions',
                'action_label': 'Manage Subscriptions',
            },
        ]

        created_count = 0
        updated_count = 0

        for template_data in templates:
            template, created = NotificationTemplate.objects.update_or_create(
                template_type=template_data['template_type'],
                defaults=template_data
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created template: {template.template_type}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'Updated template: {template.template_type}'))

        self.stdout.write(self.style.SUCCESS(
            f'\nSummary: {created_count} templates created, {updated_count} templates updated'
        ))
