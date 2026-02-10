"""
Transfer Services - Core business logic for transfer operations
"""

import logging
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum
from datetime import timedelta
import uuid

from transactions.services import WalletService
from .models import Transfer, TAC, TransferLog, TransferLimit

logger = logging.getLogger(__name__)


class TransferValidationError(Exception):
    """Custom exception for transfer validation errors"""
    pass


class TransferService:
    """Core service for transfer operations"""

    @staticmethod
    def create_transfer(account_number, amount, recipient_name, destination_type,
                       destination_details, narration=""):
        """Create a new transfer request"""
        try:
            with transaction.atomic():
                from accounts.models import Account
                
                # Get account object
                account = Account.objects.get(account_number=account_number)
                
                # Generate reference
                reference = f"TF-{uuid.uuid4().hex[:8].upper()}"
                
                # Create transfer record
                transfer = Transfer.objects.create(
                    account=account,  # FIXED: Use account object, not account_id
                    reference=reference,
                    amount=amount,
                    recipient_name=recipient_name,
                    destination_type=destination_type,
                    destination_details=destination_details,
                    narration=narration,
                    status='pending'
                )

                # Create audit log
                TransferLog.objects.create(
                    transfer=transfer,
                    log_type='created',
                    message=f'Transfer created for ${amount} to {recipient_name}',
                    metadata={
                        'account_number': account_number,
                        'amount': str(amount),
                        'destination_type': destination_type
                    }
                )

                logger.info(f"Transfer created: {transfer.reference}")
                return transfer

        except Exception as e:
            logger.error(f"Error creating transfer: {str(e)}")
            raise

    @staticmethod
    def validate_transfer(account_number, amount):
        """Validate transfer request against business rules"""
        errors = []

        try:
            # 1. Check wallet balance via WalletService
            current_balance = WalletService.get_balance(account_number)
            if current_balance < amount:
                errors.append(f"Insufficient funds. Available: ${current_balance}")

            # 2. Check daily limit
            today = timezone.now().date()
            
            # Get account object for filtering
            from accounts.models import Account
            account = Account.objects.get(account_number=account_number)
            
            daily_total = Transfer.objects.filter(
                account=account,  # FIXED: Use account object
                created_at__date=today,
                status__in=['completed', 'funds_deducted']
            ).aggregate(Sum('amount'))['amount__sum'] or 0

            daily_limit = TransferLimit.objects.filter(
                limit_type='daily',
                is_active=True
            ).first()

            if daily_limit and (daily_total + amount) > daily_limit.amount:
                errors.append(f"Daily limit exceeded. Remaining: ${daily_limit.amount - daily_total}")

            # 3. Check per-transaction limit
            tx_limit = TransferLimit.objects.filter(
                limit_type='per_transaction',
                is_active=True
            ).first()

            if tx_limit and amount > tx_limit.amount:
                errors.append(f"Maximum per transaction: ${tx_limit.amount}")

            return errors

        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            errors.append("Validation failed")
            return errors

    @staticmethod
    def generate_tac(transfer_id):
        """Generate TAC for a transfer (admin will manually send)"""
        try:
            transfer = Transfer.objects.get(id=transfer_id)

            # Generate 6-digit TAC
            tac_code = str(uuid.uuid4().int)[:6].zfill(6)

            # Create TAC record (24-hour expiry)
            tac = TAC.objects.create(
                transfer=transfer,
                code=tac_code,
                expires_at=timezone.now() + timedelta(hours=24)
            )

            # Update transfer status
            transfer.status = 'tac_sent'
            transfer.tac_sent_at = timezone.now()
            transfer.save()

            # Create audit log
            TransferLog.objects.create(
                transfer=transfer,
                log_type='tac_sent',
                message=f'TAC generated for transfer',
                metadata={'tac_code': tac_code}
            )

            logger.info(f"TAC generated for transfer {transfer.reference}: {tac_code}")

            # Return TAC for admin to manually email
            return {
                'tac_code': tac_code,
                'transfer_reference': transfer.reference,
                'account_email': transfer.account.email,
                'recipient_name': transfer.recipient_name,
                'amount': transfer.amount,
                'expires_at': tac.expires_at
            }

        except Exception as e:
            logger.error(f"Error generating TAC: {str(e)}")
            raise

    @staticmethod
    def verify_tac(transfer_id, tac_code):
        """Verify TAC code entered by client"""
        try:
            transfer = Transfer.objects.get(id=transfer_id)
            tac = TAC.objects.get(transfer=transfer, code=tac_code)

            # Validate TAC
            if not tac.is_valid():  # FIXED: Now this method exists
                raise TransferValidationError("TAC is invalid or expired")

            if tac.status != 'pending':
                raise TransferValidationError("TAC already used")

            # Mark TAC as used
            tac.status = 'used'
            tac.used_at = timezone.now()
            tac.save()

            # Update transfer status
            transfer.status = 'tac_verified'
            transfer.tac_verified_at = timezone.now()
            transfer.save()

            # Create audit log
            TransferLog.objects.create(
                transfer=transfer,
                log_type='tac_verified',
                message=f'TAC verified successfully',
                metadata={'tac_code': tac_code}
            )

            # Deduct funds from wallet
            try:
                new_balance = WalletService.debit_wallet(
                    account_number=transfer.account.account_number,  # FIXED: Get account number from account object
                    amount=transfer.amount,
                    reference=transfer.reference,
                    description=f"Transfer to {transfer.recipient_name}"
                )

                # Update transfer status
                transfer.status = 'funds_deducted'
                transfer.deducted_at = timezone.now()
                transfer.save()

                # Create audit log
                TransferLog.objects.create(
                    transfer=transfer,
                    log_type='funds_deducted',
                    message=f'Funds deducted from wallet. New balance: ${new_balance}',
                    metadata={'new_balance': str(new_balance)}
                )

                logger.info(f"Funds deducted for transfer {transfer.reference}. New balance: {new_balance}")

                return {
                    'success': True,
                    'transfer_reference': transfer.reference,
                    'new_balance': new_balance,
                    'message': 'TAC verified and funds deducted successfully'
                }

            except Exception as e:
                # Log error but don't roll back TAC verification
                logger.error(f"Error deducting funds: {str(e)}")
                TransferLog.objects.create(
                    transfer=transfer,
                    log_type='error',
                    message=f'Failed to deduct funds: {str(e)}',
                    metadata={'error': str(e)}
                )
                raise

        except TAC.DoesNotExist:
            raise TransferValidationError("Invalid TAC code")
        except Exception as e:
            logger.error(f"Error verifying TAC: {str(e)}")
            raise

    @staticmethod
    def mark_as_settled(transfer_id, external_reference, admin_notes=""):
        """Mark transfer as settled after manual external transfer"""
        try:
            transfer = Transfer.objects.get(id=transfer_id)

            # Update transfer
            transfer.status = 'completed'
            transfer.settled_at = timezone.now()
            transfer.external_reference = external_reference
            transfer.admin_notes = admin_notes
            transfer.save()

            # Create audit log
            TransferLog.objects.create(
                transfer=transfer,
                log_type='settlement_completed',
                message=f'Transfer marked as settled. External reference: {external_reference}',
                metadata={
                    'external_reference': external_reference,
                    'admin_notes': admin_notes
                }
            )

            logger.info(f"Transfer {transfer.reference} marked as settled")

            return transfer

        except Exception as e:
            logger.error(f"Error marking transfer as settled: {str(e)}")
            raise

    @staticmethod
    def get_pending_settlements():
        """Get all transfers pending manual settlement"""
        return Transfer.objects.filter(
            status='funds_deducted'
        ).select_related('account').order_by('created_at')

    @staticmethod
    def get_transfer_history(account_number, limit=50):
        """Get transfer history for an account"""
        from accounts.models import Account
        account = Account.objects.get(account_number=account_number)
        
        return Transfer.objects.filter(
            account=account  # FIXED: Use account object
        ).select_related('tac').prefetch_related('logs').order_by('-created_at')[:limit]

    @staticmethod
    def get_transfer_summary(account_number):
        """Get transfer summary statistics"""
        from accounts.models import Account
        account = Account.objects.get(account_number=account_number)
        
        today = timezone.now().date()

        transfers = Transfer.objects.filter(account=account)  # FIXED: Use account object

        summary = {
            'total_count': transfers.count(),
            'total_amount': transfers.aggregate(Sum('amount'))['amount__sum'] or 0,
            'today_count': transfers.filter(created_at__date=today).count(),
            'today_amount': transfers.filter(created_at__date=today).aggregate(Sum('amount'))['amount__sum'] or 0,
            'pending_count': transfers.filter(status='pending').count(),
            'pending_amount': transfers.filter(status='pending').aggregate(Sum('amount'))['amount__sum'] or 0,
            'completed_count': transfers.filter(status='completed').count(),
            'completed_amount': transfers.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0,
        }

        return summary


class AdminTransferService:
    """Service for admin-specific transfer operations"""

    @staticmethod
    def get_all_pending_transfers():
        """Get all transfers pending TAC generation"""
        return Transfer.objects.filter(
            status='pending'
        ).select_related('account').order_by('created_at')

    @staticmethod
    def cancel_transfer(transfer_id, reason):
        """Cancel a transfer"""
        try:
            transfer = Transfer.objects.get(id=transfer_id)

            if transfer.status not in ['pending', 'tac_sent']:
                raise TransferValidationError("Cannot cancel transfer in current status")

            transfer.status = 'cancelled'
            transfer.save()

            TransferLog.objects.create(
                transfer=transfer,
                log_type='status_change',
                message=f'Transfer cancelled: {reason}',
                metadata={'reason': reason}
            )

            logger.info(f"Transfer {transfer.reference} cancelled: {reason}")

            return transfer

        except Exception as e:
            logger.error(f"Error cancelling transfer: {str(e)}")
            raise

    @staticmethod
    def get_dashboard_stats():
        """Get admin dashboard statistics"""
        today = timezone.now().date()

        stats = {
            'total_transfers': Transfer.objects.count(),
            'today_transfers': Transfer.objects.filter(created_at__date=today).count(),
            'pending_tac': Transfer.objects.filter(status='pending').count(),
            'pending_settlement': Transfer.objects.filter(status='funds_deducted').count(),
            'total_amount_today': Transfer.objects.filter(
                created_at__date=today,
                status__in=['completed', 'funds_deducted']
            ).aggregate(Sum('amount'))['amount__sum'] or 0,
            'total_amount_all': Transfer.objects.filter(
                status__in=['completed', 'funds_deducted']
            ).aggregate(Sum('amount'))['amount__sum'] or 0,
        }

        return stats