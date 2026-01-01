# payments/management/commands/process_pending_transactions.py
"""
Management command to process pending transactions
Run: python manage.py process_pending_transactions
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from payments.models import Transaction
from payments.utils.payment_gateway import PaymentGateway
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process pending transactions'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Maximum number of transactions to process'
        )
        parser.add_argument(
            '--older-than',
            type=int,
            default=30,
            help='Process transactions older than X minutes'
        )
    
    def handle(self, *args, **options):
        limit = options['limit']
        older_than_minutes = options['older_than']
        
        cutoff_time = timezone.now() - timedelta(minutes=older_than_minutes)
        
        # Get pending transactions
        pending_transactions = Transaction.objects.filter(
            status='pending',
            created_at__lt=cutoff_time
        )[:limit]
        
        self.stdout.write(f"Processing {len(pending_transactions)} pending transactions...")
        
        processed = 0
        failed = 0
        
        for transaction in pending_transactions:
            try:
                # Try to process the payment
                result = PaymentGateway.create_payment_intent(
                    amount=transaction.amount,
                    currency=transaction.currency,
                    metadata={
                        'transaction_id': str(transaction.transaction_id),
                        'account_id': transaction.account.id
                    }
                )
                
                if result['success']:
                    transaction.status = 'processing'
                    transaction.gateway_transaction_id = result['payment_intent_id']
                    transaction.save()
                    processed += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"Started processing transaction {transaction.transaction_id}")
                    )
                else:
                    transaction.status = 'failed'
                    transaction.metadata['failure_reason'] = result.get('error', 'Unknown error')
                    transaction.save()
                    failed += 1
                    self.stdout.write(
                        self.style.ERROR(f"Failed to process transaction {transaction.transaction_id}: {result.get('error')}")
                    )
                    
            except Exception as e:
                logger.error(f"Error processing transaction {transaction.transaction_id}: {e}")
                failed += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\nProcessed: {processed}, Failed: {failed}, Total: {processed + failed}"
            )
        )