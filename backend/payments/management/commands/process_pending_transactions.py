# payments/management/commands/process_pending_transactions.py
"""
Management command to process pending transactions
Run: python manage.py process_pending_transactions
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction as db_transaction
from datetime import timedelta
from decimal import Decimal
from backend.payments.models import Transaction, Account, AuditLog
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process pending transactions'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Maximum number of transactions to process (default: 50)'
        )
        parser.add_argument(
            '--older-than',
            type=int,
            default=30,
            help='Process transactions older than X minutes (default: 30)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually processing'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force process even recent transactions'
        )
    
    def handle(self, *args, **options):
        limit = options['limit']
        older_than_minutes = options['older_than']
        dry_run = options['dry_run']
        force = options['force']
        
        if force:
            cutoff_time = timezone.now()
            self.stdout.write(
                self.style.WARNING("⚠️  FORCE MODE: Processing ALL pending transactions regardless of age")
            )
        else:
            cutoff_time = timezone.now() - timedelta(minutes=older_than_minutes)
        
        # Get pending transactions that need processing
        pending_query = Transaction.objects.filter(
            status='pending'
        )
        
        if not force:
            pending_query = pending_query.filter(created_at__lte=cutoff_time)
        
        pending_transactions = pending_query.select_related(
            'from_account', 'to_account', 'account'
        )[:limit]
        
        transaction_count = pending_transactions.count()
        
        if transaction_count == 0:
            self.stdout.write(
                self.style.SUCCESS("No pending transactions to process.")
            )
            return
        
        self.stdout.write(f"Found {transaction_count} pending transaction(s) to process...")
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING("📋 DRY RUN MODE: No transactions will be actually processed")
            )
            self._display_transaction_summary(pending_transactions)
            return
        
        processed = 0
        succeeded = 0
        failed = 0
        skipped = 0
        
        for transaction in pending_transactions:
            try:
                result = self._process_single_transaction(transaction)
                
                if result['success']:
                    succeeded += 1
                    processed += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ Processed transaction {transaction.transaction_id}: {result['message']}")
                    )
                else:
                    failed += 1
                    processed += 1
                    self.stdout.write(
                        self.style.ERROR(f"✗ Failed transaction {transaction.transaction_id}: {result.get('error', 'Unknown error')}")
                    )
                    
            except Exception as e:
                logger.error(f"Error processing transaction {transaction.transaction_id}: {e}")
                failed += 1
                processed += 1
                self.stdout.write(
                    self.style.ERROR(f"✗ Error processing transaction {transaction.transaction_id}: {str(e)}")
                )
        
        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("PROCESSING SUMMARY"))
        self.stdout.write("="*50)
        self.stdout.write(f"Total found: {transaction_count}")
        self.stdout.write(f"Processed: {processed}")
        self.stdout.write(f"Succeeded: {succeeded}")
        self.stdout.write(f"Failed: {failed}")
        self.stdout.write(f"Skipped: {skipped}")
        
        if succeeded > 0:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Successfully processed {succeeded} transaction(s)")
            )
        if failed > 0:
            self.stdout.write(
                self.style.ERROR(f"❌ Failed to process {failed} transaction(s)")
            )
    
    def _process_single_transaction(self, transaction):
        """Process a single transaction based on its type"""
        
        if transaction.transaction_type == 'deposit':
            return self._process_deposit(transaction)
        elif transaction.transaction_type == 'withdrawal':
            return self._process_withdrawal(transaction)
        elif transaction.transaction_type == 'transfer':
            return self._process_transfer(transaction)
        elif transaction.transaction_type == 'payment':
            return self._process_payment(transaction)
        else:
            return {
                'success': False,
                'error': f"Unknown transaction type: {transaction.transaction_type}"
            }
    
    def _process_deposit(self, transaction):
        """Process a deposit transaction"""
        try:
            # Validate the transaction
            if not transaction.account:
                return {
                    'success': False,
                    'error': 'No account specified for deposit'
                }
            
            if not transaction.account.is_active:
                return {
                    'success': False,
                    'error': 'Account is not active'
                }
            
            # Process in a database transaction
            with db_transaction.atomic():
                # Update transaction status
                transaction.status = 'completed'
                transaction.save()
                
                # Update account balance
                transaction.account.balance += transaction.amount
                transaction.account.save()
                
                # Log the action
                AuditLog.objects.create(
                    user=transaction.account.user,
                    action='deposit_processed',
                    details={
                        'transaction_id': str(transaction.transaction_id),
                        'account_id': transaction.account.id,
                        'account_number': transaction.account.account_number,
                        'amount': str(transaction.amount),
                        'currency': transaction.currency,
                        'description': transaction.description
                    }
                )
            
            return {
                'success': True,
                'message': f'Deposited {transaction.amount} {transaction.currency} to account {transaction.account.account_number}'
            }
            
        except Exception as e:
            # Mark as failed
            transaction.status = 'failed'
            transaction.save()
            
            # Log the failure
            if transaction.account:
                AuditLog.objects.create(
                    user=transaction.account.user,
                    action='deposit_failed',
                    details={
                        'transaction_id': str(transaction.transaction_id),
                        'account_id': transaction.account.id,
                        'error': str(e),
                        'amount': str(transaction.amount)
                    }
                )
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def _process_withdrawal(self, transaction):
        """Process a withdrawal transaction"""
        try:
            # Validate the transaction
            if not transaction.account:
                return {
                    'success': False,
                    'error': 'No account specified for withdrawal'
                }
            
            if not transaction.account.is_active:
                return {
                    'success': False,
                    'error': 'Account is not active'
                }
            
            if transaction.account.balance < transaction.amount:
                return {
                    'success': False,
                    'error': f'Insufficient funds. Available: {transaction.account.balance}, Required: {transaction.amount}'
                }
            
            # Process in a database transaction
            with db_transaction.atomic():
                # Update transaction status
                transaction.status = 'completed'
                transaction.save()
                
                # Update account balance
                transaction.account.balance -= transaction.amount
                transaction.account.save()
                
                # Log the action
                AuditLog.objects.create(
                    user=transaction.account.user,
                    action='withdrawal_processed',
                    details={
                        'transaction_id': str(transaction.transaction_id),
                        'account_id': transaction.account.id,
                        'account_number': transaction.account.account_number,
                        'amount': str(transaction.amount),
                        'currency': transaction.currency,
                        'description': transaction.description
                    }
                )
            
            return {
                'success': True,
                'message': f'Withdrew {transaction.amount} {transaction.currency} from account {transaction.account.account_number}'
            }
            
        except Exception as e:
            # Mark as failed
            transaction.status = 'failed'
            transaction.save()
            
            # Log the failure
            if transaction.account:
                AuditLog.objects.create(
                    user=transaction.account.user,
                    action='withdrawal_failed',
                    details={
                        'transaction_id': str(transaction.transaction_id),
                        'account_id': transaction.account.id,
                        'error': str(e),
                        'amount': str(transaction.amount)
                    }
                )
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def _process_transfer(self, transaction):
        """Process a transfer transaction"""
        try:
            # Validate the transaction
            if not transaction.from_account:
                return {
                    'success': False,
                    'error': 'No source account specified for transfer'
                }
            
            if not transaction.to_account:
                return {
                    'success': False,
                    'error': 'No destination account specified for transfer'
                }
            
            if not transaction.from_account.is_active:
                return {
                    'success': False,
                    'error': 'Source account is not active'
                }
            
            if not transaction.to_account.is_active:
                return {
                    'success': False,
                    'error': 'Destination account is not active'
                }
            
            if transaction.from_account.balance < transaction.amount:
                return {
                    'success': False,
                    'error': f'Insufficient funds. Available: {transaction.from_account.balance}, Required: {transaction.amount}'
                }
            
            if transaction.from_account.currency != transaction.to_account.currency:
                return {
                    'success': False,
                    'error': f'Currency mismatch. Source: {transaction.from_account.currency}, Target: {transaction.to_account.currency}'
                }
            
            if transaction.from_account.id == transaction.to_account.id:
                return {
                    'success': False,
                    'error': 'Cannot transfer to the same account'
                }
            
            # Process in a database transaction
            with db_transaction.atomic():
                # Lock both accounts for update
                from_account = Account.objects.select_for_update().get(pk=transaction.from_account.pk)
                to_account = Account.objects.select_for_update().get(pk=transaction.to_account.pk)
                
                # Double-check balance
                if from_account.balance < transaction.amount:
                    return {
                        'success': False,
                        'error': f'Insufficient funds after lock. Available: {from_account.balance}, Required: {transaction.amount}'
                    }
                
                # Update transaction status
                transaction.status = 'completed'
                transaction.save()
                
                # Update account balances
                from_account.balance -= transaction.amount
                from_account.save()
                
                to_account.balance += transaction.amount
                to_account.save()
                
                # Log the action
                AuditLog.objects.create(
                    user=from_account.user,
                    action='transfer_processed',
                    details={
                        'transaction_id': str(transaction.transaction_id),
                        'from_account_id': from_account.id,
                        'from_account_number': from_account.account_number,
                        'to_account_id': to_account.id,
                        'to_account_number': to_account.account_number,
                        'amount': str(transaction.amount),
                        'currency': transaction.currency,
                        'description': transaction.description
                    }
                )
            
            return {
                'success': True,
                'message': f'Transferred {transaction.amount} {transaction.currency} from {transaction.from_account.account_number} to {transaction.to_account.account_number}'
            }
            
        except Exception as e:
            # Mark as failed
            transaction.status = 'failed'
            transaction.save()
            
            # Log the failure
            if transaction.from_account:
                AuditLog.objects.create(
                    user=transaction.from_account.user,
                    action='transfer_failed',
                    details={
                        'transaction_id': str(transaction.transaction_id),
                        'from_account_id': transaction.from_account.id,
                        'to_account_id': transaction.to_account.id if transaction.to_account else None,
                        'error': str(e),
                        'amount': str(transaction.amount)
                    }
                )
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def _process_payment(self, transaction):
        """Process a payment transaction (similar to withdrawal)"""
        try:
            # Validate the transaction
            if not transaction.account:
                return {
                    'success': False,
                    'error': 'No account specified for payment'
                }
            
            if not transaction.account.is_active:
                return {
                    'success': False,
                    'error': 'Account is not active'
                }
            
            if transaction.account.balance < transaction.amount:
                return {
                    'success': False,
                    'error': f'Insufficient funds. Available: {transaction.account.balance}, Required: {transaction.amount}'
                }
            
            # Process in a database transaction
            with db_transaction.atomic():
                # Update transaction status
                transaction.status = 'completed'
                transaction.save()
                
                # Update account balance
                transaction.account.balance -= transaction.amount
                transaction.account.save()
                
                # Log the action
                AuditLog.objects.create(
                    user=transaction.account.user,
                    action='payment_processed',
                    details={
                        'transaction_id': str(transaction.transaction_id),
                        'account_id': transaction.account.id,
                        'account_number': transaction.account.account_number,
                        'amount': str(transaction.amount),
                        'currency': transaction.currency,
                        'description': transaction.description,
                        'recipient': transaction.to_account.account_number if transaction.to_account else 'External'
                    }
                )
            
            return {
                'success': True,
                'message': f'Processed payment of {transaction.amount} {transaction.currency} from account {transaction.account.account_number}'
            }
            
        except Exception as e:
            # Mark as failed
            transaction.status = 'failed'
            transaction.save()
            
            # Log the failure
            if transaction.account:
                AuditLog.objects.create(
                    user=transaction.account.user,
                    action='payment_failed',
                    details={
                        'transaction_id': str(transaction.transaction_id),
                        'account_id': transaction.account.id,
                        'error': str(e),
                        'amount': str(transaction.amount)
                    }
                )
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def _display_transaction_summary(self, transactions):
        """Display summary of transactions that would be processed"""
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.WARNING("DRY RUN - TRANSACTION SUMMARY"))
        self.stdout.write("="*50)
        
        type_counts = {}
        total_amount = Decimal('0.00')
        
        for transaction in transactions:
            # Count by type
            t_type = transaction.transaction_type
            type_counts[t_type] = type_counts.get(t_type, 0) + 1
            
            # Sum amounts
            total_amount += transaction.amount
            
            # Display transaction details
            self.stdout.write(f"\nTransaction: {transaction.transaction_id}")
            self.stdout.write(f"  Type: {t_type}")
            self.stdout.write(f"  Amount: {transaction.amount} {transaction.currency}")
            self.stdout.write(f"  Created: {transaction.created_at}")
            
            if transaction.from_account:
                self.stdout.write(f"  From: {transaction.from_account.account_number}")
            if transaction.to_account:
                self.stdout.write(f"  To: {transaction.to_account.account_number}")
            if transaction.account:
                self.stdout.write(f"  Account: {transaction.account.account_number}")
        
        self.stdout.write("\n" + "="*50)
        self.stdout.write("SUMMARY STATISTICS")
        self.stdout.write("="*50)
        
        for t_type, count in type_counts.items():
            self.stdout.write(f"{t_type.title()}: {count}")
        
        self.stdout.write(f"\nTotal transactions: {len(transactions)}")
        self.stdout.write(f"Total amount: {total_amount}")
        self.stdout.write("\n" + "="*50)