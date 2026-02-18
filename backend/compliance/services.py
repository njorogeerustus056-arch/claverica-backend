"""
compliance/services.py - Business logic for compliance
"""
from django.utils import timezone
from django.db import transaction, models  #  ADD 'models' import
from django.core.exceptions import ValidationError
from .models import TransferRequest, TransferLog, ComplianceSetting


class TransferService:
    """Service for transfer operations"""

    @staticmethod
    def create_transfer_request(account, amount, recipient_name,
                               destination_type, destination_details,
                               narration=""):
        """Create a new transfer request with validation"""

        # Validate amount
        if amount <= 0:
            raise ValidationError("Amount must be positive")

        # Check daily limit
        daily_limit = ComplianceSetting.objects.filter(
            setting_type='daily_limit',
            is_active=True
        ).first()

        if daily_limit:
            today = timezone.now().date()
            today_total = TransferRequest.objects.filter(
                account=account,
                created_at__date=today,
                status__in=['completed', 'tac_verified']
            ).aggregate(models.Sum('amount'))['amount__sum'] or 0

            if today_total + amount > float(daily_limit.value):
                raise ValidationError(f"Daily limit exceeded. Remaining: ${float(daily_limit.value) - today_total}")

        # Create transfer
        transfer = TransferRequest.objects.create(
            account=account,
            amount=amount,
            recipient_name=recipient_name,
            destination_type=destination_type,
            destination_details=destination_details,
            narration=narration,
            status='pending_tac'
        )

        # Create log
        TransferLog.objects.create(
            transfer=transfer,
            log_type='created',
            message=f'Transfer request created for ${amount}',
            metadata={
                'amount': str(amount),
                'recipient': recipient_name,
                'destination_type': destination_type
            }
        )

        return transfer

    @staticmethod
    def get_transfer_status(transfer_id):
        """Get detailed transfer status"""
        transfer = TransferRequest.objects.get(id=transfer_id)

        status_info = {
            'reference': transfer.reference,
            'status': transfer.status,
            'amount': transfer.amount,
            'recipient_name': transfer.recipient_name,
            'created_at': transfer.created_at,
            'tac_generated': bool(transfer.tac_code),  #  FIXED: Use tac_code not tac_generated
            'tac_expires_at': transfer.tac_expires_at,
            'requires_kyc': transfer.requires_kyc,
            'kyc_verified': transfer.kyc_verified,
            'next_steps': []
        }

        # Add next steps based on status
        if transfer.status == 'pending_tac':
            status_info['next_steps'].append('Admin will generate TAC code')
            status_info['next_steps'].append('You will receive TAC via email/SMS')

        elif transfer.status == 'tac_generated':
            status_info['next_steps'].append('TAC generated, awaiting admin to send')

        elif transfer.status == 'tac_sent':
            status_info['next_steps'].append('TAC sent, please enter code in dashboard')
            status_info['next_steps'].append('TAC expires in 24 hours')

        elif transfer.status == 'tac_verified':
            status_info['next_steps'].append('TAC verified, funds will be deducted')
            status_info['next_steps'].append('Admin will process bank transfer')

        elif transfer.status == 'pending_settlement':
            status_info['next_steps'].append('Funds deducted, awaiting bank transfer')
            status_info['next_steps'].append('Processing time: 1-2 business days')

        elif transfer.status == 'completed':
            status_info['next_steps'].append('Transfer completed')
            if transfer.external_reference:
                status_info['external_reference'] = transfer.external_reference

        elif transfer.status == 'kyc_required':
            status_info['next_steps'].append('KYC required for this amount')
            status_info['next_steps'].append('Please submit KYC documents')

        return status_info

    @staticmethod
    def get_user_transfers(account, limit=50):
        """Get transfer history for account"""
        return TransferRequest.objects.filter(
            account=account
        ).select_related('account').prefetch_related('logs').order_by('-created_at')[:limit]

    @staticmethod
    def get_pending_admin_actions():
        """Get counts of pending admin actions"""
        return {
            'pending_tac': TransferRequest.objects.filter(status='pending_tac').count(),
            'tac_generated': TransferRequest.objects.filter(status='tac_generated').count(),
            'tac_verified': TransferRequest.objects.filter(status='tac_verified').count(),
            'kyc_required': TransferRequest.objects.filter(status='kyc_required').count(),
        }


class ComplianceService:
    """Service for compliance settings and rules"""

    @staticmethod
    def get_kyc_threshold():
        """Get current KYC threshold"""
        try:
            setting = ComplianceSetting.objects.get(
                setting_type='kyc_threshold',
                is_active=True
            )
            return float(setting.value)
        except ComplianceSetting.DoesNotExist:
            return 1500.00  # Default

    @staticmethod
    def check_transfer_limits(account, amount):
        """Check if transfer exceeds limits"""
        errors = []

        # Get limits
        daily_limit = ComplianceSetting.objects.filter(
            setting_type='daily_limit',
            is_active=True
        ).first()

        weekly_limit = ComplianceSetting.objects.filter(
            setting_type='weekly_limit',
            is_active=True
        ).first()

        # Check daily limit
        if daily_limit:
            today = timezone.now().date()
            today_total = TransferRequest.objects.filter(
                account=account,
                created_at__date=today,
                status__in=['completed', 'tac_verified']
            ).aggregate(models.Sum('amount'))['amount__sum'] or 0

            if today_total + amount > float(daily_limit.value):
                errors.append(f"Daily limit: ${daily_limit.value}. Used: ${today_total}")

        # Check weekly limit
        if weekly_limit:
            week_ago = timezone.now() - timezone.timedelta(days=7)
            weekly_total = TransferRequest.objects.filter(
                account=account,
                created_at__gte=week_ago,
                status__in=['completed', 'tac_verified']
            ).aggregate(models.Sum('amount'))['amount__sum'] or 0

            if weekly_total + amount > float(weekly_limit.value):
                errors.append(f"Weekly limit: ${weekly_limit.value}. Used: ${weekly_total}")

        return errors

    @staticmethod
    def update_settings(settings_data, updated_by):
        """Update compliance settings"""
        for setting_type, value in settings_data.items():
            setting, created = ComplianceSetting.objects.update_or_create(
                setting_type=setting_type,
                defaults={
                    'value': str(value),
                    'updated_by': updated_by
                }
            )

        return True