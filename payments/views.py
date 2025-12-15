from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Q
from django.shortcuts import get_object_or_404
from datetime import date, timedelta
from decimal import Decimal

from .models import (
    Account, Transaction, Card, Beneficiary,
    SavingsGoal, CryptoWallet, Subscription
)
from .serializers import (
    AccountSerializer, TransactionSerializer, TransactionCreateSerializer,
    CardSerializer, BeneficiarySerializer, SavingsGoalSerializer,
    CryptoWalletSerializer, SubscriptionSerializer, AccountBalanceSerializer,
    TransferRequestSerializer
)


class AccountViewSet(viewsets.ModelViewSet):
    """Manage user accounts"""
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['get'])
    def balance(self, request, pk=None):
        """Get detailed balance information"""
        account = self.get_object()
        
        # Calculate pending transactions
        pending_count = Transaction.objects.filter(
            account=account,
            status__in=['pending', 'processing']
        ).count()
        
        # Calculate total savings
        total_savings = SavingsGoal.objects.filter(
            account=account,
            status='active'
        ).aggregate(total=Sum('current_amount'))['total'] or Decimal('0.00')
        
        balance_data = {
            'balance': account.balance,
            'available_balance': account.available_balance,
            'currency': account.currency,
            'pending_transactions': pending_count,
            'total_savings': total_savings
        }
        
        serializer = AccountBalanceSerializer(balance_data)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """Get account summary with all related data"""
        account = self.get_object()
        
        # Recent transactions
        recent_transactions = Transaction.objects.filter(account=account)[:10]
        
        # Active cards
        active_cards = Card.objects.filter(account=account, status='active')
        
        # Savings goals
        savings_goals = SavingsGoal.objects.filter(account=account, status='active')
        
        # Monthly spending
        thirty_days_ago = date.today() - timedelta(days=30)
        monthly_spending = Transaction.objects.filter(
            account=account,
            transaction_type__in=['payment', 'withdrawal'],
            created_at__gte=thirty_days_ago,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        return Response({
            'account': AccountSerializer(account).data,
            'recent_transactions': TransactionSerializer(recent_transactions, many=True).data,
            'active_cards': CardSerializer(active_cards, many=True).data,
            'savings_goals': SavingsGoalSerializer(savings_goals, many=True).data,
            'monthly_spending': monthly_spending
        })


class TransactionViewSet(viewsets.ModelViewSet):
    """Manage transactions"""
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TransactionCreateSerializer
        return TransactionSerializer
    
    def get_queryset(self):
        user_accounts = Account.objects.filter(user=self.request.user)
        return Transaction.objects.filter(account__in=user_accounts)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.method == 'POST':
            account_id = self.request.data.get('account_id')
            if account_id:
                context['account'] = get_object_or_404(
                    Account, 
                    id=account_id, 
                    user=self.request.user
                )
        return context
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent transactions"""
        account_id = request.query_params.get('account_id')
        limit = int(request.query_params.get('limit', 20))
        
        queryset = self.get_queryset()
        if account_id:
            queryset = queryset.filter(account_id=account_id)
        
        transactions = queryset[:limit]
        serializer = self.get_serializer(transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending transactions"""
        queryset = self.get_queryset().filter(status__in=['pending', 'processing'])
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a pending transaction"""
        transaction = self.get_object()
        
        if transaction.status not in ['pending', 'processing']:
            return Response(
                {'error': 'Only pending transactions can be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        transaction.status = 'cancelled'
        transaction.save()
        
        # Refund amount to account if already deducted
        if transaction.transaction_type in ['withdrawal', 'transfer', 'payment']:
            transaction.account.available_balance += transaction.amount
            transaction.account.save()
        
        return Response({'status': 'Transaction cancelled'})


class CardViewSet(viewsets.ModelViewSet):
    """Manage cards"""
    serializer_class = CardSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user_accounts = Account.objects.filter(user=self.request.user)
        return Card.objects.filter(account__in=user_accounts)
    
    @action(detail=True, methods=['post'])
    def block(self, request, pk=None):
        """Block a card"""
        card = self.get_object()
        card.status = 'blocked'
        card.save()
        return Response({'status': 'Card blocked'})
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a card"""
        card = self.get_object()
        card.status = 'active'
        card.save()
        return Response({'status': 'Card activated'})


class BeneficiaryViewSet(viewsets.ModelViewSet):
    """Manage beneficiaries"""
    serializer_class = BeneficiarySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Beneficiary.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def favorites(self, request):
        """Get favorite beneficiaries"""
        favorites = self.get_queryset().filter(is_favorite=True)
        serializer = self.get_serializer(favorites, many=True)
        return Response(serializer.data)


class SavingsGoalViewSet(viewsets.ModelViewSet):
    """Manage savings goals"""
    serializer_class = SavingsGoalSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user_accounts = Account.objects.filter(user=self.request.user)
        return SavingsGoal.objects.filter(account__in=user_accounts)
    
    @action(detail=True, methods=['post'])
    def deposit(self, request, pk=None):
        """Deposit to savings goal"""
        goal = self.get_object()
        amount = Decimal(request.data.get('amount', 0))
        
        if amount <= 0:
            return Response(
                {'error': 'Invalid amount'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check account balance
        if goal.account.available_balance < amount:
            return Response(
                {'error': 'Insufficient balance'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update balances
        goal.current_amount += amount
        goal.account.available_balance -= amount
        
        # Check if goal is completed
        if goal.current_amount >= goal.target_amount:
            goal.status = 'completed'
            goal.completed_at = date.today()
        
        goal.save()
        goal.account.save()
        
        # Create transaction record
        Transaction.objects.create(
            account=goal.account,
            transaction_type='investment',
            amount=amount,
            currency=goal.currency,
            status='completed',
            description=f"Deposit to savings goal: {goal.name}"
        )
        
        return Response(SavingsGoalSerializer(goal).data)
    
    @action(detail=True, methods=['post'])
    def withdraw(self, request, pk=None):
        """Withdraw from savings goal"""
        goal = self.get_object()
        amount = Decimal(request.data.get('amount', 0))
        
        if amount <= 0 or amount > goal.current_amount:
            return Response(
                {'error': 'Invalid amount'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update balances
        goal.current_amount -= amount
        goal.account.available_balance += amount
        goal.save()
        goal.account.save()
        
        # Create transaction record
        Transaction.objects.create(
            account=goal.account,
            transaction_type='withdrawal',
            amount=amount,
            currency=goal.currency,
            status='completed',
            description=f"Withdrawal from savings goal: {goal.name}"
        )
        
        return Response(SavingsGoalSerializer(goal).data)


class CryptoWalletViewSet(viewsets.ReadOnlyModelViewSet):
    """View crypto wallets"""
    serializer_class = CryptoWalletSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user_accounts = Account.objects.filter(user=self.request.user)
        return CryptoWallet.objects.filter(account__in=user_accounts)


class SubscriptionViewSet(viewsets.ModelViewSet):
    """Manage subscriptions"""
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user_accounts = Account.objects.filter(user=self.request.user)
        return Subscription.objects.filter(account__in=user_accounts)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get subscriptions due in next 7 days"""
        seven_days = date.today() + timedelta(days=7)
        upcoming = self.get_queryset().filter(
            next_billing_date__lte=seven_days,
            status='active'
        )
        serializer = self.get_serializer(upcoming, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel_subscription(self, request, pk=None):
        """Cancel a subscription"""
        subscription = self.get_object()
        subscription.status = 'cancelled'
        subscription.save()
        return Response({'status': 'Subscription cancelled'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def quick_transfer(request):
    """Quick transfer endpoint"""
    serializer = TransferRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Get user's primary account
    try:
        account = Account.objects.get(
            user=request.user,
            account_type='checking',
            is_active=True
        )
    except Account.DoesNotExist:
        return Response(
            {'error': 'No active account found'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get recipient account
    try:
        recipient_account = Account.objects.get(
            account_number=serializer.validated_data['recipient_account_number']
        )
    except Account.DoesNotExist:
        return Response(
            {'error': 'Recipient account not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    amount = serializer.validated_data['amount']
    
    # Check balance
    if account.available_balance < amount:
        return Response(
            {'error': 'Insufficient balance'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create transaction
    transaction = Transaction.objects.create(
        account=account,
        transaction_type='transfer',
        amount=amount,
        currency=serializer.validated_data.get('currency', 'USD'),
        recipient_account=recipient_account,
        recipient_name=recipient_account.user.get_full_name(),
        description=serializer.validated_data.get('description', ''),
        status='completed'
    )
    
    # Update balances
    account.balance -= amount
    account.available_balance -= amount
    account.save()
    
    recipient_account.balance += amount
    recipient_account.available_balance += amount
    recipient_account.save()
    
    return Response(
        TransactionSerializer(transaction).data,
        status=status.HTTP_201_CREATED
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics"""
    user_accounts = Account.objects.filter(user=request.user)
    
    # Total balance across all accounts
    total_balance = user_accounts.aggregate(total=Sum('balance'))['total'] or Decimal('0.00')
    
    # Recent transactions (last 30 days)
    thirty_days_ago = date.today() - timedelta(days=30)
    recent_transactions_count = Transaction.objects.filter(
        account__in=user_accounts,
        created_at__gte=thirty_days_ago
    ).count()
    
    # Active cards
    active_cards_count = Card.objects.filter(
        account__in=user_accounts,
        status='active'
    ).count()
    
    # Savings goals progress
    savings_goals = SavingsGoal.objects.filter(
        account__in=user_accounts,
        status='active'
    )
    total_savings_target = savings_goals.aggregate(total=Sum('target_amount'))['total'] or Decimal('0.00')
    total_savings_current = savings_goals.aggregate(total=Sum('current_amount'))['total'] or Decimal('0.00')
    
    # Monthly spending
    monthly_spending = Transaction.objects.filter(
        account__in=user_accounts,
        transaction_type__in=['payment', 'withdrawal'],
        created_at__gte=thirty_days_ago,
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    return Response({
        'total_balance': total_balance,
        'recent_transactions_count': recent_transactions_count,
        'active_cards_count': active_cards_count,
        'savings_progress': {
            'target': total_savings_target,
            'current': total_savings_current,
            'percentage': (total_savings_current / total_savings_target * 100) if total_savings_target > 0 else 0
        },
        'monthly_spending': monthly_spending
    })
