from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Q
from django.shortcuts import get_object_or_404

from .models import (
    CryptoAsset, CryptoWallet, CryptoTransaction,
    CryptoAddress, FiatPlatform, UserFiatAccount
)
from .serializers import (
    CryptoAssetSerializer, CryptoWalletSerializer,
    CryptoTransactionSerializer, CryptoTransactionCreateSerializer,
    CryptoAddressSerializer, FiatPlatformSerializer,
    UserFiatAccountSerializer, UserFiatAccountCreateSerializer
)


class CryptoAssetViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for cryptocurrency assets"""
    queryset = CryptoAsset.objects.filter(is_active=True)
    serializer_class = CryptoAssetSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['symbol', 'name']
    filterset_fields = ['blockchain', 'is_tradable']
    
    @action(detail=False, methods=['get'])
    def top_assets(self, request):
        """Get top cryptocurrencies by market cap"""
        assets = self.get_queryset().order_by('-market_cap')[:20]
        serializer = self.get_serializer(assets, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def price_history(self, request, pk=None):
        """Get price history for an asset"""
        asset = self.get_object()
        # You would typically fetch from an external API
        return Response({
            'asset': asset.symbol,
            'history': []  # Add price history data here
        })


class CryptoWalletViewSet(viewsets.ModelViewSet):
    """ViewSet for user crypto wallets"""
    serializer_class = CryptoWalletSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return CryptoWallet.objects.filter(user=self.request.user, is_active=True)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """Get all transactions for a wallet"""
        wallet = self.get_object()
        transactions = CryptoTransaction.objects.filter(
            Q(from_wallet=wallet) | Q(to_wallet=wallet)
        ).order_by('-created_at')
        serializer = CryptoTransactionSerializer(transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def portfolio(self, request):
        """Get user's crypto portfolio summary"""
        wallets = self.get_queryset()
        
        total_balance_usd = wallets.aggregate(total=Sum('balance_usd'))['total'] or 0
        
        portfolio = []
        for wallet in wallets:
            portfolio.append({
                'symbol': wallet.asset.symbol,
                'name': wallet.asset.name,
                'balance': wallet.balance,
                'balance_usd': wallet.balance_usd,
                'current_price': wallet.asset.current_price_usd,
                'allocation': (wallet.balance_usd / total_balance_usd * 100) if total_balance_usd > 0 else 0
            })
        
        return Response({
            'total_balance_usd': total_balance_usd,
            'wallet_count': wallets.count(),
            'portfolio': portfolio
        })


class CryptoTransactionViewSet(viewsets.ModelViewSet):
    """ViewSet for crypto transactions"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return CryptoTransaction.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CryptoTransactionCreateSerializer
        return CryptoTransactionSerializer
    
    def perform_create(self, serializer):
        transaction = serializer.save(user=self.request.user)
        
        # Update wallet balances based on transaction type
        if transaction.transaction_type in ['send', 'withdrawal'] and transaction.from_wallet:
            wallet = transaction.from_wallet
            wallet.available_balance -= transaction.amount
            wallet.locked_balance += transaction.amount
            wallet.save()
        
        elif transaction.transaction_type in ['receive', 'deposit'] and transaction.to_wallet:
            wallet = transaction.to_wallet
            wallet.balance += transaction.amount
            wallet.available_balance += transaction.amount
            wallet.save()
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm a pending transaction"""
        transaction = self.get_object()
        
        if transaction.status != 'pending':
            return Response(
                {"error": "Only pending transactions can be confirmed"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update transaction status
        transaction.status = 'completed'
        transaction.save()
        
        # Update wallet balances
        if transaction.transaction_type in ['send', 'withdrawal'] and transaction.from_wallet:
            wallet = transaction.from_wallet
            wallet.locked_balance -= transaction.amount
            wallet.save()
        
        return Response({"message": "Transaction confirmed successfully"})
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get transaction statistics"""
        transactions = self.get_queryset()
        
        total_count = transactions.count()
        completed = transactions.filter(status='completed').count()
        pending = transactions.filter(status='pending').count()
        
        total_volume = transactions.filter(status='completed').aggregate(
            total=Sum('amount_usd')
        )['total'] or 0
        
        return Response({
            'total_transactions': total_count,
            'completed': completed,
            'pending': pending,
            'total_volume_usd': total_volume
        })


class CryptoAddressViewSet(viewsets.ModelViewSet):
    """ViewSet for crypto addresses"""
    serializer_class = CryptoAddressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return CryptoAddress.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FiatPlatformViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for fiat platforms"""
    queryset = FiatPlatform.objects.filter(is_active=True)
    serializer_class = FiatPlatformSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'platform_type']


class UserFiatAccountViewSet(viewsets.ModelViewSet):
    """ViewSet for user fiat accounts"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserFiatAccount.objects.filter(user=self.request.user, is_active=True)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserFiatAccountCreateSerializer
        return UserFiatAccountSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify a fiat account"""
        account = self.get_object()
        
        # In production, you would implement actual verification logic
        account.is_verified = True
        account.save()
        
        return Response({"message": "Account verified successfully"})