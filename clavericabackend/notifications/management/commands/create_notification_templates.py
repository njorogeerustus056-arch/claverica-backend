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
            # Add other templates as needed...
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
