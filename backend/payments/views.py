# payments/views.py - COMPLETE CORRECTED VERSION WITH FIX

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Q
from django.shortcuts import get_object_or_404
from datetime import date, timedelta
from decimal import Decimal
from django.db import transaction as db_transaction
import uuid

# CORRECTED IMPORTS - Only models that exist
from .models import Account, Transaction, Card, PaymentMethod

# CORRECTED SERIALIZER IMPORTS - Only serializers that exist
from .serializers import (
    AccountSerializer, TransactionSerializer, TransactionCreateSerializer,
    CardSerializer, AccountBalanceSerializer, TransferRequestSerializer,
    PaymentMethodSerializer
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
        
        with db_transaction.atomic():
            # Use select_for_update for consistency
            account = Account.objects.select_for_update().get(pk=account.pk)
            
            pending_count = Transaction.objects.filter(
                account=account,
                status__in=['pending', 'processing']
            ).count()
            
            balance_data = {
                'balance': account.balance,
                'available_balance': account.available_balance,
                'currency': account.currency,
                'pending_transactions': pending_count,
            }
        
        serializer = AccountBalanceSerializer(balance_data)
        return Response(serializer.data)


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
    
    def create(self, request, *args, **kwargs):
        """Create transaction with idempotency check"""
        idempotency_key = request.headers.get('Idempotency-Key')
        
        if idempotency_key:
            # Check for existing transaction with same idempotency key
            existing = Transaction.objects.filter(
                idempotency_key=idempotency_key
            ).first()
            
            if existing:
                return Response(
                    TransactionSerializer(existing).data,
                    status=status.HTTP_200_OK
                )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with db_transaction.atomic():
            # Add idempotency key if provided
            if idempotency_key:
                serializer.validated_data['idempotency_key'] = idempotency_key
            
            transaction = serializer.save()
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            TransactionSerializer(transaction).data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a pending transaction"""
        transaction = self.get_object()
        
        if transaction.status not in ['pending', 'processing']:
            return Response(
                {'error': 'Only pending transactions can be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with db_transaction.atomic():
            # Lock transaction and account
            transaction = Transaction.objects.select_for_update().get(pk=transaction.pk)
            account = Account.objects.select_for_update().get(pk=transaction.account.pk)
            
            transaction.status = 'cancelled'
            transaction.save()
            
            # Refund amount to account if already deducted
            if transaction.transaction_type in ['withdrawal', 'transfer', 'payment']:
                account.available_balance += transaction.amount
                account.save()
        
        return Response({'status': 'Transaction cancelled'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def quick_transfer(request):
    """Quick transfer endpoint with atomic operations - FIXED VERSION"""
    serializer = TransferRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with db_transaction.atomic():
            # Get the sender's account - FIXED: Use filter().first() instead of get()
            account = Account.objects.select_for_update().filter(
                user=request.user,
                is_active=True
            ).first()
            
            if not account:
                return Response(
                    {'error': 'No active account found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            recipient_account = Account.objects.select_for_update().get(
                account_number=serializer.validated_data['recipient_account_number']
            )
            
            amount = serializer.validated_data['amount']
            
            # Check balance
            if account.available_balance < amount:
                return Response(
                    {'error': 'Insufficient balance'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check currency match
            if account.currency != recipient_account.currency:
                return Response(
                    {'error': 'Currency mismatch'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create transaction
            transaction = Transaction.objects.create(
                account=account,
                transaction_type='transfer',
                amount=amount,
                currency=serializer.validated_data.get('currency', 'USD'),
                recipient_account=recipient_account,
                recipient_name=recipient_account.user.get_full_name() or recipient_account.user.email,
                description=serializer.validated_data.get('description', ''),
                status='completed',
                idempotency_key=request.headers.get('Idempotency-Key', str(uuid.uuid4()))
            )
            
            # Update balances atomically
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
            
    except Account.DoesNotExist:
        return Response(
            {'error': 'Account not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class CardViewSet(viewsets.ModelViewSet):
    """Manage cards - SECURE VERSION"""
    serializer_class = CardSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user_accounts = Account.objects.filter(user=self.request.user)
        return Card.objects.filter(account__in=user_accounts)
    
    def create(self, request, *args, **kwargs):
        """Create card - should integrate with payment gateway"""
        # In production, this should call Stripe/PayPal to create a token
        # NEVER accept raw card details directly!
        
        # Example with Stripe:
        # stripe_token = request.data.get('stripe_token')
        # stripe.Customer.create_source(customer_id, source=stripe_token)
        
        return Response(
            {'error': 'Card creation requires payment gateway integration'},
            status=status.HTTP_501_NOT_IMPLEMENTED
        )
    
    @action(detail=True, methods=['post'])
    def block(self, request, pk=None):
        """Block a card"""
        with db_transaction.atomic():
            card = Card.objects.select_for_update().get(pk=pk)
            card.status = 'blocked'
            card.save()
            
            # Call payment gateway to block card
            # stripe.Customer.delete_source(customer_id, card.token)
            
        return Response({'status': 'Card blocked'})


class PaymentMethodViewSet(viewsets.ModelViewSet):
    """Manage payment methods"""
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return PaymentMethod.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics"""
    try:
        user_accounts = Account.objects.filter(user=request.user)
        
        # Total balance
        total_balance = sum(acc.balance for acc in user_accounts)
        
        # Recent transactions
        recent_transactions = Transaction.objects.filter(
            account__in=user_accounts
        ).order_by('-created_at')[:5]
        
        # Active cards
        active_cards = Card.objects.filter(
            account__in=user_accounts,
            status='active'
        ).count()
        
        # Pending transactions
        pending_transactions = Transaction.objects.filter(
            account__in=user_accounts,
            status__in=['pending', 'processing']
        ).count()
        
        stats = {
            'total_balance': float(total_balance),
            'currency': 'USD',
            'active_cards': active_cards,
            'pending_transactions': pending_transactions,
            'recent_transactions': TransactionSerializer(recent_transactions, many=True).data
        }
        
        return Response(stats)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )