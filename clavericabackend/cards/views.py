"""
Django REST Framework views for Cards app
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from decimal import Decimal
import random
from datetime import datetime, timedelta

from .models import Card, Transaction, CardStatus
from .serializers import (
    CardSerializer, CardCreateSerializer, CardUpdateSerializer,
    TransactionSerializer, TopUpSerializer, CardBalanceSerializer
)


class CardViewSet(viewsets.ModelViewSet):
    """ViewSet for managing cards"""
    
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CardCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CardUpdateSerializer
        return CardSerializer
    
    def get_queryset(self):
        """Return cards for current user only"""
        return Card.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Create a new card with generated details"""
        # Generate card details
        card_number = self._generate_card_number()
        cvv = self._generate_cvv()
        expiry_date = self._generate_expiry_date()
        
        # Check if this should be primary card
        is_primary = not Card.objects.filter(user=self.request.user).exists()
        
        # Save card
        serializer.save(
            user=self.request.user,
            card_number=card_number,
            last_four=card_number[-4:],
            cvv=cvv,
            expiry_date=expiry_date,
            is_primary=is_primary,
            balance=Decimal('0.00'),
            status=CardStatus.ACTIVE
        )
    
    def perform_update(self, serializer):
        """Update card with special handling for is_primary"""
        if 'is_primary' in serializer.validated_data and serializer.validated_data['is_primary']:
            # Remove primary from other cards
            Card.objects.filter(user=self.request.user).exclude(
                id=serializer.instance.id
            ).update(is_primary=False)
        
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def freeze(self, request, pk=None):
        """Freeze a card"""
        card = self.get_object()
        card.status = CardStatus.FROZEN
        card.save()
        
        return Response({
            'message': 'Card frozen successfully',
            'card': CardSerializer(card).data
        })
    
    @action(detail=True, methods=['post'])
    def unfreeze(self, request, pk=None):
        """Unfreeze a card"""
        card = self.get_object()
        card.status = CardStatus.ACTIVE
        card.save()
        
        return Response({
            'message': 'Card unfrozen successfully',
            'card': CardSerializer(card).data
        })
    
    @action(detail=True, methods=['post'])
    def top_up(self, request, pk=None):
        """Top up card balance from user account"""
        card = self.get_object()
        serializer = TopUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        amount = serializer.validated_data['amount']
        
        # Get user's account balance from payments app
        try:
            from payments.models import Account
            account = Account.objects.filter(
                user=request.user,
                is_active=True
            ).first()
            
            if not account:
                return Response(
                    {'error': 'No active account found'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if account.balance < amount:
                return Response(
                    {'error': 'Insufficient account balance'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Transfer from account to card
            account.balance -= amount
            account.save()
            
        except ImportError:
            # Fallback if payments app not available
            return Response(
                {'error': 'Account management not available'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        card.balance += amount
        card.save()
        
        # Create transaction record
        Transaction.objects.create(
            user=request.user,
            card=card,
            amount=amount,
            merchant='Card Top-up',
            category='transfer',
            transaction_type='credit',
            status='completed',
            description=f'Top-up to card ending in {card.last_four}'
        )
        
        balance_data = {
            'card_balance': card.balance,
            'account_balance': account.balance if 'account' in locals() else Decimal('0.00')
        }
        
        return Response({
            'message': 'Card topped up successfully',
            **balance_data
        })
    
    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """Get transactions for a specific card"""
        card = self.get_object()
        transactions = Transaction.objects.filter(card=card)
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)
    
    @staticmethod
    def _generate_card_number():
        """Generate a 16-digit card number"""
        return ''.join([str(random.randint(0, 9)) for _ in range(16)])
    
    @staticmethod
    def _generate_cvv():
        """Generate a 3-digit CVV"""
        return ''.join([str(random.randint(0, 9)) for _ in range(3)])
    
    @staticmethod
    def _generate_expiry_date():
        """Generate expiry date (5 years from now)"""
        future_date = datetime.now() + timedelta(days=1825)
        return future_date.strftime("%m/%y")


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing transactions"""
    
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return transactions for current user only"""
        return Transaction.objects.filter(user=self.request.user)
