# payments/views.py - UPDATED WITH WALLET SYSTEM
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Q
from django.shortcuts import get_object_or_404
from decimal import Decimal, InvalidOperation
from django.db import transaction as db_transaction
from django.contrib.auth import get_user_model
import logging
from datetime import datetime

from .models import (
    Account, Transaction, Card, AuditLog,
    MainBusinessWallet, EmployeePlatformWallet,
    PaymentTransactionNotification, WithdrawalRequest, ActivityFeed
)
from .serializers import (
    AccountSerializer, AccountBalanceSerializer,
    TransactionSerializer, QuickTransferSerializer, 
    CardSerializer, DepositWithdrawalSerializer,
    TransactionStatusSerializer,
    MainBusinessWalletSerializer, EmployeePlatformWalletSerializer,
    PaymentTransactionNotificationSerializer, WithdrawalRequestSerializer,
    ActivityFeedSerializer, EmployerPaymentSerializer,
    WithdrawalRequestCreateSerializer, TACVerificationSerializer,
    AgentCallScheduleSerializer, ComplianceFormSerializer
)
from .services import (
    PaymentService,
    generate_reference_code,
    format_payment_message,
    send_payment_notification
)

User = get_user_model()
logger = logging.getLogger(__name__)


class AccountViewSet(viewsets.ModelViewSet):
    """Manage user accounts"""
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Account.objects.filter(user=self.request.user).order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def perform_destroy(self, instance):
        """Override delete to deactivate instead of hard delete"""
        if instance.balance != Decimal('0.00'):
            raise ValueError("Cannot deactivate account with non-zero balance")
        instance.is_active = False
        instance.save()
    
    @action(detail=True, methods=['get'])
    def balance(self, request, pk=None):
        """Get account balance"""
        account = self.get_object()
        serializer = AccountBalanceSerializer(account)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def deposit(self, request, pk=None):
        """Deposit funds into account"""
        account = self.get_object()
        
        serializer = DepositWithdrawalSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            amount = Decimal(str(serializer.validated_data['amount']))
            description = serializer.validated_data.get('description', 'Deposit')
            
            if amount <= Decimal('0'):
                return Response(
                    {'error': 'Amount must be greater than 0'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            with db_transaction.atomic():
                # Create deposit transaction
                transaction = Transaction.objects.create(
                    account=account,
                    amount=amount,
                    currency=account.currency,
                    transaction_type='deposit',
                    description=description,
                    status='completed'
                )
                
                # Update account balance
                account.balance += amount
                account.available_balance += amount
                account.save()
                
                # Log the deposit
                AuditLog.objects.create(
                    user=request.user,
                    action='deposit_made',
                    details={
                        'account_id': account.id,
                        'account_number': account.account_number,
                        'amount': str(amount),
                        'transaction_id': transaction.transaction_id
                    }
                )
            
            return Response(
                TransactionSerializer(transaction).data,
                status=status.HTTP_201_CREATED
            )
            
        except InvalidOperation:
            return Response(
                {'error': 'Invalid amount format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Deposit failed: {str(e)}")
            return Response(
                {'error': 'Deposit failed. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def withdraw(self, request, pk=None):
        """Withdraw funds from account"""
        account = self.get_object()
        
        serializer = DepositWithdrawalSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            amount = Decimal(str(serializer.validated_data['amount']))
            description = serializer.validated_data.get('description', 'Withdrawal')
            
            if amount <= Decimal('0'):
                return Response(
                    {'error': 'Amount must be greater than 0'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check available balance, not just balance
            if account.available_balance < amount:
                return Response(
                    {'error': 'Insufficient available funds'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            with db_transaction.atomic():
                # Create withdrawal transaction
                transaction = Transaction.objects.create(
                    account=account,
                    amount=amount,
                    currency=account.currency,
                    transaction_type='withdrawal',
                    description=description,
                    status='completed'
                )
                
                # Update account balance
                account.balance -= amount
                account.available_balance -= amount
                account.save()
                
                # Log the withdrawal
                AuditLog.objects.create(
                    user=request.user,
                    action='withdrawal_made',
                    details={
                        'account_id': account.id,
                        'account_number': account.account_number,
                        'amount': str(amount),
                        'transaction_id': transaction.transaction_id
                    }
                )
            
            return Response(
                TransactionSerializer(transaction).data,
                status=status.HTTP_201_CREATED
            )
            
        except InvalidOperation:
            return Response(
                {'error': 'Invalid amount format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Withdrawal failed: {str(e)}")
            return Response(
                {'error': 'Withdrawal failed. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TransactionViewSet(viewsets.ModelViewSet):
    """View and create transactions"""
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Get transactions where user is involved using account and recipient_account
        return Transaction.objects.filter(
            Q(account__user=user) | 
            Q(recipient_account__user=user)
        ).select_related(
            'account', 'recipient_account', 
            'account__user', 'recipient_account__user'
        ).order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        """Handle transaction creation"""
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get validated data
            data = serializer.validated_data
            account = data.get('account')
            recipient_account = data.get('recipient_account')
            amount = data['amount']
            transaction_type = data.get('transaction_type', 'transfer')
            description = data.get('description', '')
            
            # Handle different transaction types
            if transaction_type == 'deposit':
                # Deposit: account receives money
                if not account:
                    return Response(
                        {'error': 'Account is required for deposit'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                with db_transaction.atomic():
                    # Create transaction
                    transaction = Transaction.objects.create(
                        account=account,
                        amount=amount,
                        currency=account.currency,
                        transaction_type='deposit',
                        description=description,
                        status='completed'
                    )
                    
                    # Update balance
                    account.balance += amount
                    account.available_balance += amount
                    account.save()
                    
            elif transaction_type == 'withdrawal':
                # Withdrawal: account sends money (no recipient)
                if not account:
                    return Response(
                        {'error': 'Account is required for withdrawal'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                if account.available_balance < amount:
                    return Response(
                        {'error': 'Insufficient available funds'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                with db_transaction.atomic():
                    # Create transaction
                    transaction = Transaction.objects.create(
                        account=account,
                        amount=amount,
                        currency=account.currency,
                        transaction_type='withdrawal',
                        description=description,
                        status='completed'
                    )
                    
                    # Update balance
                    account.balance -= amount
                    account.available_balance -= amount
                    account.save()
                    
            elif transaction_type == 'transfer':
                # Transfer: account sends to recipient_account
                if not account or not recipient_account:
                    return Response(
                        {'error': 'Both sender and recipient accounts are required for transfer'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Check if sender account belongs to user
                if account.user != request.user:
                    return Response(
                        {'error': 'You can only transfer from your own accounts'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                # Check if recipient account is active
                if not recipient_account.is_active:
                    return Response(
                        {'error': 'Recipient account is not active'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Use the account's transfer_funds method
                transaction = account.transfer_funds(
                    to_account=recipient_account,
                    amount=amount,
                    description=description
                )
                
            else:
                return Response(
                    {'error': f'Invalid transaction type: {transaction_type}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Serialize and return the created transaction
            output_serializer = TransactionSerializer(transaction)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Transaction creation failed: {str(e)}")
            return Response(
                {'error': 'Transaction creation failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update transaction status (admin/owner only)"""
        transaction = self.get_object()
        
        # Check if user has permission to update this transaction
        user = request.user
        
        # User must be either sender or receiver
        is_owner = (
            (transaction.account and transaction.account.user == user) or
            (transaction.recipient_account and transaction.recipient_account.user == user)
        )
        
        if not is_owner and not user.is_staff:
            return Response(
                {'error': 'You do not have permission to update this transaction'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = TransactionStatusSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            new_status = serializer.validated_data['status']
            notes = serializer.validated_data.get('notes', '')
            
            # Update transaction status
            old_status = transaction.status
            transaction.status = new_status
            transaction.description = f"{transaction.description}\nStatus Update: {new_status}. Notes: {notes}"
            transaction.save()
            
            # Log the status change
            AuditLog.objects.create(
                user=request.user,
                action='transaction_status_updated',
                details={
                    'transaction_id': transaction.transaction_id,
                    'old_status': old_status,
                    'new_status': new_status,
                    'notes': notes
                }
            )
            
            return Response(
                TransactionSerializer(transaction).data,
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Status update failed: {str(e)}")
            return Response(
                {'error': 'Failed to update transaction status'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def quick_transfer(self, request):
        """Quick transfer endpoint"""
        serializer = QuickTransferSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            to_account_number = serializer.validated_data['to_account_number']
            amount = Decimal(str(serializer.validated_data['amount']))
            description = serializer.validated_data.get('description', 'Quick Transfer')
            
            if amount <= Decimal('0'):
                return Response(
                    {'error': 'Amount must be greater than 0'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get sender's primary account (first active account)
            sender_account = Account.objects.filter(
                user=request.user,
                is_active=True
            ).first()
            
            if not sender_account:
                return Response(
                    {'error': 'No active account found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get recipient account
            try:
                recipient_account = Account.objects.get(
                    account_number=to_account_number,
                    is_active=True
                )
            except Account.DoesNotExist:
                return Response(
                    {'error': 'Recipient account not found or inactive'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if transferring to self
            if sender_account.id == recipient_account.id:
                return Response(
                    {'error': 'Cannot transfer to the same account'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Use the model's transfer_funds method
            transaction = sender_account.transfer_funds(
                to_account=recipient_account,
                amount=amount,
                description=description
            )
            
            # Log the transfer
            AuditLog.objects.create(
                user=request.user,
                action='quick_transfer_made',
                details={
                    'from_account': sender_account.account_number,
                    'to_account': recipient_account.account_number,
                    'amount': str(amount),
                    'transaction_id': transaction.transaction_id
                }
            )
            
            return Response(
                TransactionSerializer(transaction).data,
                status=status.HTTP_201_CREATED
            )
            
        except Account.DoesNotExist:
            return Response(
                {'error': 'Account not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except InvalidOperation:
            return Response(
                {'error': 'Invalid amount format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Quick transfer failed: {str(e)}")
            return Response(
                {'error': 'Transfer failed. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CardViewSet(viewsets.ModelViewSet):
    """Manage cards"""
    serializer_class = CardSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user_accounts = Account.objects.filter(user=self.request.user, is_active=True)
        return Card.objects.filter(account__in=user_accounts).order_by('-created_at')
    
    def perform_create(self, serializer):
        """Create a new card - ensure it's associated with user's account"""
        account = serializer.validated_data.get('account')
        
        # Verify the account belongs to the user
        if account.user != self.request.user:
            raise permissions.PermissionDenied("You can only add cards to your own accounts")
        
        serializer.save()
        
        # Log card creation (masked for security)
        AuditLog.objects.create(
            user=self.request.user,
            action='card_created',
            details={
                'account_id': account.id,
                'card_type': serializer.validated_data.get('card_type'),
                'last_four': serializer.validated_data.get('last_four'),
                'status': 'active'
            }
        )
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a card"""
        card = self.get_object()
        
        old_status = card.status
        card.status = 'inactive'
        card.save()
        
        # Log card deactivation
        AuditLog.objects.create(
            user=request.user,
            action='card_deactivated',
            details={
                'card_id': card.id,
                'last_four': card.last_four,
                'old_status': old_status,
                'new_status': card.status
            }
        )
        
        return Response({
            'message': 'Card deactivated successfully',
            'card_id': card.id,
            'status': card.status
        })


# ============================================
# WALLET SYSTEM VIEWSETS
# ============================================

class MainBusinessWalletViewSet(viewsets.ModelViewSet):
    """Manage main business wallets (employers)"""
    serializer_class = MainBusinessWalletSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return MainBusinessWallet.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        # Check if user already has a main business wallet
        if MainBusinessWallet.objects.filter(user=self.request.user).exists():
            raise serializers.ValidationError("You already have a main business wallet")
        
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['get'])
    def balance(self, request, pk=None):
        """Get wallet balance"""
        wallet = self.get_object()
        return Response({
            'wallet_number': wallet.wallet_number,
            'total_balance': str(wallet.total_balance),
            'available_balance': str(wallet.available_balance),
            'currency': wallet.currency,
            'display_name': wallet.display_name
        })
    
    @action(detail=True, methods=['post'])
    def replenish(self, request, pk=None):
        """Replenish wallet from connected bank"""
        wallet = self.get_object()
        amount = Decimal(request.data.get('amount', '0'))
        
        if amount <= Decimal('0'):
            return Response(
                {'error': 'Amount must be greater than 0'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # In production, this would connect to bank API
            with db_transaction.atomic():
                wallet.total_balance += amount
                wallet.available_balance += amount
                wallet.save()
                
                # Log the replenishment
                AuditLog.objects.create(
                    user=request.user,
                    action='wallet_replenished',
                    details={
                        'wallet_number': wallet.wallet_number,
                        'amount': str(amount),
                        'bank': wallet.connected_bank_name,
                        'new_balance': str(wallet.total_balance)
                    }
                )
            
            return Response({
                'message': f'Wallet replenished with ${amount}',
                'new_balance': str(wallet.total_balance),
                'available_balance': str(wallet.available_balance)
            })
            
        except Exception as e:
            logger.error(f"Wallet replenish failed: {str(e)}")
            return Response(
                {'error': 'Wallet replenishment failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EmployeePlatformWalletViewSet(viewsets.ModelViewSet):
    """Manage employee platform wallets"""
    serializer_class = EmployeePlatformWalletSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return EmployeePlatformWallet.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        # Check if user already has an employee wallet
        if EmployeePlatformWallet.objects.filter(user=self.request.user).exists():
            raise serializers.ValidationError("You already have an employee platform wallet")
        
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['get'])
    def balance(self, request, pk=None):
        """Get wallet balance"""
        wallet = self.get_object()
        return Response({
            'wallet_number': wallet.wallet_number,
            'platform_balance': str(wallet.platform_balance),
            'available_for_withdrawal': str(wallet.available_for_withdrawal),
            'pending_withdrawal': str(wallet.pending_withdrawal),
            'currency': wallet.currency,
            'display_name': wallet.display_name
        })
    
    @action(detail=True, methods=['post'])
    def request_withdrawal(self, request, pk=None):
        """Request withdrawal from platform wallet"""
        wallet = self.get_object()
        
        serializer = WithdrawalRequestCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            amount = Decimal(str(serializer.validated_data['amount']))
            bank_account_id = serializer.validated_data.get('bank_account_id')
            notes = serializer.validated_data.get('notes', '')
            
            # Get bank account
            if bank_account_id:
                bank_account = Account.objects.get(
                    id=bank_account_id,
                    user=request.user
                )
            else:
                # Use preferred bank or get first active account
                bank_account = wallet.preferred_bank or \
                    Account.objects.filter(user=request.user, is_active=True).first()
            
            if not bank_account:
                return Response(
                    {'error': 'No bank account found for withdrawal'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create withdrawal request
            withdrawal = wallet.request_withdrawal(amount, bank_account)
            withdrawal.save()
            
            # Create activity feed entry
            ActivityFeed.objects.create(
                user=request.user,
                activity_type='withdrawal_request',
                reference=withdrawal.withdrawal_reference,
                amount=amount,
                display_text=f"🏦 Withdrawal requested: ${amount}",
                emoji='🏦',
                color_class='text-blue-600'
            )
            
            return Response(
                WithdrawalRequestSerializer(withdrawal).data,
                status=status.HTTP_201_CREATED
            )
            
        except Account.DoesNotExist:
            return Response(
                {'error': 'Bank account not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Withdrawal request failed: {str(e)}")
            return Response(
                {'error': 'Withdrawal request failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WithdrawalRequestViewSet(viewsets.ReadOnlyModelViewSet):
    """View withdrawal requests"""
    serializer_class = WithdrawalRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Employees see their own requests
        # Agents/admins see assigned requests
        user = self.request.user
        
        if user.is_staff:
            # Staff can see all or assigned requests
            return WithdrawalRequest.objects.all().order_by('-created_at')
        else:
            # Regular users see their own requests
            return WithdrawalRequest.objects.filter(
                employee_wallet__user=user
            ).order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def submit_compliance(self, request, pk=None):
        """Submit compliance form for withdrawal"""
        withdrawal = self.get_object()
        
        serializer = ComplianceFormSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        if withdrawal.status != 'pending':
            return Response(
                {'error': 'Withdrawal is not in pending state'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            withdrawal.compliance_form_filled = True
            withdrawal.status = 'compliance_check'
            withdrawal.save()
            
            # Create activity feed entry
            ActivityFeed.objects.create(
                user=withdrawal.employee_wallet.user,
                activity_type='compliance_started',
                reference=withdrawal.withdrawal_reference,
                display_text="⏳ Compliance form submitted",
                emoji='⏳',
                color_class='text-yellow-600'
            )
            
            return Response({
                'message': 'Compliance form submitted successfully',
                'status': withdrawal.status
            })
            
        except Exception as e:
            logger.error(f"Compliance submission failed: {str(e)}")
            return Response(
                {'error': 'Compliance submission failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def verify_tac(self, request, pk=None):
        """Verify TAC code for withdrawal"""
        withdrawal = self.get_object()
        
        serializer = TACVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        if withdrawal.status != 'tac_verification':
            return Response(
                {'error': 'Withdrawal is not in TAC verification stage'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tac_code = serializer.validated_data['tac_code']
        
        if withdrawal.tac_code != tac_code:
            return Response(
                {'error': 'Invalid TAC code'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            withdrawal.tac_verified_at = timezone.now()
            withdrawal.status = 'processing'
            withdrawal.save()
            
            # Process the withdrawal (transfer to bank)
            with db_transaction.atomic():
                # Deduct from wallet
                wallet = withdrawal.employee_wallet
                wallet.pending_withdrawal -= withdrawal.amount
                wallet.save()
                
                # Create bank transfer transaction
                transaction = Transaction.objects.create(
                    account=wallet.user.accounts.first(),  # Use first account
                    amount=withdrawal.amount,
                    currency=withdrawal.currency,
                    transaction_type='withdrawal',
                    description=f"Withdrawal to bank: {withdrawal.bank_account.account_number}",
                    status='processing'
                )
                
                withdrawal.transaction_reference = transaction.transaction_id
                withdrawal.processed_at = timezone.now()
                withdrawal.save()
            
            # Create activity feed entry
            ActivityFeed.objects.create(
                user=withdrawal.employee_wallet.user,
                activity_type='withdrawal_completed',
                reference=withdrawal.withdrawal_reference,
                amount=withdrawal.amount,
                display_text=f"✅ Withdrawal processed: ${withdrawal.amount}",
                emoji='✅',
                color_class='text-green-600'
            )
            
            return Response({
                'message': 'TAC verified successfully. Withdrawal is being processed.',
                'status': withdrawal.status,
                'transaction_reference': withdrawal.transaction_reference
            })
            
        except Exception as e:
            logger.error(f"TAC verification failed: {str(e)}")
            return Response(
                {'error': 'TAC verification failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PaymentTransactionNotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """View payment notifications"""
    serializer_class = PaymentTransactionNotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return PaymentTransactionNotification.objects.filter(
            receiver=self.request.user
        ).order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def mark_delivered(self, request, pk=None):
        """Mark notification as delivered"""
        notification = self.get_object()
        notification.website_delivered = True
        notification.delivered_at = timezone.now()
        notification.save()
        
        return Response({
            'message': 'Notification marked as delivered',
            'notification_id': notification.id
        })


class ActivityFeedViewSet(viewsets.ReadOnlyModelViewSet):
    """View activity feed"""
    serializer_class = ActivityFeedSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ActivityFeed.objects.filter(
            user=self.request.user
        ).order_by('-created_at')


# ============================================
# WALLET OPERATION VIEWS
# ============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pay_employee(request):
    """Employer pays employee"""
    serializer = EmployerPaymentSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        employee_email = serializer.validated_data['employee_email']
        amount = Decimal(str(serializer.validated_data['amount']))
        description = serializer.validated_data.get('description', 'Payment from employer')
        sender_display_name = serializer.validated_data.get('sender_display_name', 'ecoveraLTD')
        
        # Get employer's main business wallet
        employer_wallet = MainBusinessWallet.objects.get(user=request.user)
        
        # Get employee's platform wallet
        employee = User.objects.get(email=employee_email)
        employee_wallet = EmployeePlatformWallet.objects.get(user=employee)
        
        # Check employer has sufficient funds
        if not employer_wallet.has_sufficient_funds(amount):
            return Response(
                {'error': f'Insufficient funds. Available: ${employer_wallet.available_balance}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with db_transaction.atomic():
            # Deduct from employer wallet
            employer_wallet.deduct_funds(amount, description)
            
            # Add to employee wallet
            employee_wallet.add_funds(amount, 'employer_payment')
            
            # Generate reference code
            reference_code = generate_reference_code()
            
            # Create payment notification
            notification = PaymentService.create_payment_notification(
                sender=request.user,
                receiver=employee,
                amount=amount,
                sender_display_name=sender_display_name,
                description=description,
                reference_code=reference_code
            )
            
            # Send notifications
            send_payment_notification(notification)
            
            # Create activity feed entries
            # Employer activity
            ActivityFeed.objects.create(
                user=request.user,
                activity_type='payment_sent',
                reference=reference_code,
                amount=amount,
                display_text=f"↓ Sent: ${amount} to {employee.email}",
                emoji='📤',
                color_class='text-blue-600'
            )
            
            # Employee activity
            ActivityFeed.objects.create(
                user=employee,
                activity_type='payment_received',
                reference=reference_code,
                amount=amount,
                display_text=f"↑ +${amount} (ClaveRica LTD)",
                emoji='😊',
                color_class='text-green-600'
            )
        
        return Response({
            'message': 'Payment successful',
            'reference_code': reference_code,
            'amount': str(amount),
            'employee': employee.email,
            'notification': PaymentTransactionNotificationSerializer(notification).data
        })
        
    except MainBusinessWallet.DoesNotExist:
        return Response(
            {'error': 'Employer wallet not found. You need to set up a main business wallet first.'},
            status=status.HTTP_404_NOT_FOUND
        )
    except EmployeePlatformWallet.DoesNotExist:
        return Response(
            {'error': 'Employee wallet not found. The employee needs to set up their platform wallet.'},
            status=status.HTTP_404_NOT_FOUND
        )
    except User.DoesNotExist:
        return Response(
            {'error': 'Employee not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Employee payment failed: {str(e)}")
        return Response(
            {'error': 'Payment failed. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def schedule_agent_call(request):
    """Schedule agent video call for withdrawal"""
    serializer = AgentCallScheduleSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        withdrawal_id = serializer.validated_data['withdrawal_request_id']
        call_date = serializer.validated_data['call_date']
        notes = serializer.validated_data.get('notes', '')
        
        withdrawal = WithdrawalRequest.objects.get(
            id=withdrawal_id,
            employee_wallet__user=request.user  # User must own the withdrawal
        )
        
        if withdrawal.status != 'compliance_check':
            return Response(
                {'error': 'Withdrawal must be in compliance check stage'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        withdrawal.agent_call_scheduled = True
        withdrawal.agent_call_date = call_date
        withdrawal.status = 'agent_call'
        withdrawal.agent_notes = notes
        withdrawal.save()
        
        # Create activity feed entry
        ActivityFeed.objects.create(
            user=request.user,
            activity_type='agent_call',
            reference=withdrawal.withdrawal_reference,
            display_text=f"📞 Agent call scheduled: {call_date.strftime('%b %d, %Y %I:%M %p')}",
            emoji='📞',
            color_class='text-purple-600'
        )
        
        return Response({
            'message': 'Agent call scheduled successfully',
            'call_date': call_date,
            'withdrawal_reference': withdrawal.withdrawal_reference
        })
        
    except WithdrawalRequest.DoesNotExist:
        return Response(
            {'error': 'Withdrawal request not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Agent call scheduling failed: {str(e)}")
        return Response(
            {'error': 'Failed to schedule agent call'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_wallet_dashboard(request):
    """Get complete wallet dashboard data"""
    user = request.user
    
    try:
        # Get main business wallet if exists
        main_wallet = None
        if hasattr(user, 'main_business_wallet'):
            main_wallet = MainBusinessWalletSerializer(user.main_business_wallet).data
        
        # Get employee platform wallet if exists
        employee_wallet = None
        if hasattr(user, 'employee_platform_wallet'):
            employee_wallet = EmployeePlatformWalletSerializer(user.employee_platform_wallet).data
        
        # Get recent notifications
        recent_notifications = PaymentTransactionNotification.objects.filter(
            receiver=user
        ).order_by('-created_at')[:10]
        
        # Get recent activity feed
        recent_activity = ActivityFeed.objects.filter(
            user=user
        ).order_by('-created_at')[:20]
        
        # Get pending withdrawal requests
        pending_withdrawals = WithdrawalRequest.objects.filter(
            employee_wallet__user=user,
            status__in=['pending', 'compliance_check', 'agent_call', 'tac_verification']
        ).order_by('-created_at')
        
        # Calculate total received this month
        from django.utils import timezone
        from datetime import timedelta
        
        one_month_ago = timezone.now() - timedelta(days=30)
        
        monthly_payments = PaymentTransactionNotification.objects.filter(
            receiver=user,
            notification_type='payment_received',
            created_at__gte=one_month_ago
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        return Response({
            'main_business_wallet': main_wallet,
            'employee_platform_wallet': employee_wallet,
            'recent_notifications': PaymentTransactionNotificationSerializer(recent_notifications, many=True).data,
            'recent_activity': ActivityFeedSerializer(recent_activity, many=True).data,
            'pending_withdrawals': WithdrawalRequestSerializer(pending_withdrawals, many=True).data,
            'stats': {
                'monthly_payments': str(monthly_payments),
                'total_notifications': recent_notifications.count(),
                'pending_withdrawals_count': pending_withdrawals.count()
            }
        })
        
    except Exception as e:
        logger.error(f"Wallet dashboard failed: {str(e)}")
        return Response(
            {'error': 'Failed to load wallet dashboard'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================
# EXISTING DASHBOARD VIEW (UPDATED)
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics - UPDATED WITH WALLET INFO"""
    user = request.user
    
    try:
        # Get user accounts
        accounts = Account.objects.filter(user=user, is_active=True)
        
        # Calculate total balance
        total_balance_result = accounts.aggregate(total=Sum('balance'))
        total_balance = total_balance_result['total'] or Decimal('0.00')
        
        # Get account details
        account_details = AccountBalanceSerializer(accounts, many=True).data
        
        # Get recent transactions
        recent_transactions = Transaction.objects.filter(
            Q(account__user=user) | 
            Q(recipient_account__user=user)
        ).order_by('-created_at')[:10]
        
        # Count active cards
        active_cards = Card.objects.filter(
            account__user=user,
            status='active'
        ).count()
        
        # Count pending transactions
        pending_transactions = Transaction.objects.filter(
            Q(account__user=user),
            status='pending'
        ).count()
        
        # Calculate monthly totals
        from django.utils import timezone
        from datetime import timedelta
        
        one_month_ago = timezone.now() - timedelta(days=30)
        
        monthly_deposits = Transaction.objects.filter(
            account__user=user,
            transaction_type='deposit',
            status='completed',
            created_at__gte=one_month_ago
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        monthly_withdrawals = Transaction.objects.filter(
            account__user=user,
            transaction_type='withdrawal',
            status='completed',
            created_at__gte=one_month_ago
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Get wallet info if exists
        wallet_info = {}
        if hasattr(user, 'main_business_wallet'):
            wallet_info['main_business_wallet'] = {
                'balance': str(user.main_business_wallet.total_balance),
                'available': str(user.main_business_wallet.available_balance),
                'wallet_number': user.main_business_wallet.wallet_number
            }
        
        if hasattr(user, 'employee_platform_wallet'):
            wallet_info['employee_platform_wallet'] = {
                'balance': str(user.employee_platform_wallet.platform_balance),
                'available_for_withdrawal': str(user.employee_platform_wallet.available_for_withdrawal),
                'wallet_number': user.employee_platform_wallet.wallet_number
            }
        
        return Response({
            'total_balance': str(total_balance),
            'currency': 'USD',
            'accounts': account_details,
            'active_cards': active_cards,
            'pending_transactions': pending_transactions,
            'monthly_deposits': str(monthly_deposits),
            'monthly_withdrawals': str(monthly_withdrawals),
            'recent_transactions': TransactionSerializer(recent_transactions, many=True).data,
            'account_count': accounts.count(),
            'wallet_info': wallet_info
        })
        
    except Exception as e:
        logger.error(f"Dashboard stats failed: {str(e)}")
        return Response(
            {'error': 'Failed to load dashboard data'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )