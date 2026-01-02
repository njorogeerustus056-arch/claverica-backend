# payments/views.py - CORRECTED VERSION
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Q
from django.shortcuts import get_object_or_404
from decimal import Decimal, InvalidOperation
from django.db import transaction as db_transaction
import logging

from .models import Account, Transaction, Card, AuditLog
from .serializers import (
    AccountSerializer, AccountBalanceSerializer,
    TransactionSerializer, QuickTransferSerializer, 
    CardSerializer, DepositWithdrawalSerializer,
    TransactionStatusSerializer
)

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


class TransactionViewSet(viewsets.ModelViewSet):  # CHANGED: ReadOnlyModelViewSet -> ModelViewSet
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics"""
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
        
        return Response({
            'total_balance': str(total_balance),
            'currency': 'USD',
            'accounts': account_details,
            'active_cards': active_cards,
            'pending_transactions': pending_transactions,
            'monthly_deposits': str(monthly_deposits),
            'monthly_withdrawals': str(monthly_withdrawals),
            'recent_transactions': TransactionSerializer(recent_transactions, many=True).data,
            'account_count': accounts.count()
        })
        
    except Exception as e:
        logger.error(f"Dashboard stats failed: {str(e)}")
        return Response(
            {'error': 'Failed to load dashboard data'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )