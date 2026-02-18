"""
Django REST Framework views for Cards app
"""

from rest_framework import viewsets, generics, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.db import transaction
from decimal import Decimal
import random
from datetime import datetime, timedelta
from .models import Card, CardTransaction, CardType, CardStatus
from .serializers import (
    CardSerializer,
    CardCreateSerializer,
    CardUpdateSerializer,
    CardTransactionSerializer,
    CardTransactionCreateSerializer,
    CardBalanceSerializer,
    TopUpSerializer
)


def generate_card_number():
    """Generate a 16-digit card number"""
    return ''.join([str(random.randint(0, 9)) for _ in range(16)])


def generate_expiry_date():
    """Generate expiry date (5 years from now)"""
    future_date = datetime.now() + timedelta(days=1825)
    return future_date.strftime("%m/%y")


class CardViewSet(viewsets.ModelViewSet):
    """ViewSet for Card model"""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # FIXED: Filter by account instead of user
        return Card.objects.filter(account=self.request.user).order_by('-is_primary', '-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return CardCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CardUpdateSerializer
        return CardSerializer

    def perform_create(self, serializer):
        # Generate card details
        card_number = generate_card_number()
        expiry_date = generate_expiry_date()

        # Check if this should be primary card
        # FIXED: Use account filter
        existing_cards = Card.objects.filter(account=self.request.user).count()
        is_primary = existing_cards == 0

        # Save card with generated details
        serializer.save(
            account=self.request.user,
            card_number=card_number,
            last_four=card_number[-4:],
            expiry_date=expiry_date,
            status=CardStatus.ACTIVE,
            is_primary=is_primary
        )

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

    # Top-up function removed - Cards don't have separate balance


class CardTransactionViewSet(viewsets.ModelViewSet):
    """ViewSet for CardTransaction model"""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # FIXED: Filter by account
        return CardTransaction.objects.filter(
            account=self.request.user
        ).order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return CardTransactionCreateSerializer
        return CardTransactionSerializer

    def perform_create(self, serializer):
        # FIXED: Save with account from request
        user_account = self.request.user  # This is Account model instance
        serializer.save(account=user_account)


class UserCardsAPIView(generics.ListAPIView):
    """API view to get all cards for current user"""

    permission_classes = [IsAuthenticated]
    serializer_class = CardSerializer

    def get_queryset(self):
        # FIXED: Filter by account
        return Card.objects.filter(account=self.request.user).order_by('-is_primary', '-created_at')


class CardBalanceAPIView(generics.RetrieveAPIView):
    """API view to get card balance - FIXED"""

    permission_classes = [IsAuthenticated]
    serializer_class = CardBalanceSerializer

    def get_object(self):
        card_id = self.kwargs.get('card_id')
        try:
            # FIXED: Filter by account
            card = Card.objects.get(id=card_id, account=self.request.user)
            return {
                'card_balance': card.balance,
                'wallet_balance': card.account.wallet.balance if hasattr(card.account, 'wallet') else Decimal('0.00')
            }
        except Card.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Card not found")


# ========== ADD THIS AT THE VERY END OF views.py ==========
from rest_framework.decorators import api_view

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_cards_simple(request):
    """Simple cards endpoint for frontend"""
    try:
        user = request.user
        cards = Card.objects.filter(account=user).order_by('-is_primary', '-created_at')

        cards_data = []
        for card in cards:
            cards_data.append({
                'id': card.id,
                'type': card.card_type,
                'last4': getattr(card, 'last_four', '4242')[-4:],
                'balance': float(getattr(card, 'balance', 0.0)),
                'expiry': getattr(card, 'expiry_date', '12/25'),
                'isActive': card.status == 'active',
                'color': card.color_scheme or 'blue',
                'brand': 'Visa' if card.card_number.startswith('4') else 'Mastercard',
                'cardholderName': card.display_name,
                'maskedNumber': card.masked_number,
                'isPrimary': card.is_primary
            })

        return Response({
            'cards': cards_data,
            'count': len(cards_data)
        })

    except Exception as e:
        return Response({
            'cards': [],
            'count': 0,
            'error': str(e)
        })
