# crypto/views.py - UPDATED FOR COMPLIANCE INTEGRATION

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Q
from django.shortcuts import get_object_or_404
from decimal import Decimal

from .models import (
    CryptoAsset, CryptoWallet, CryptoTransaction,
    CryptoAddress, FiatPlatform, UserFiatAccount,
    CryptoComplianceFlag, CryptoAuditLog
)
from .serializers import (
    CryptoAssetSerializer, CryptoWalletSerializer,
    CryptoTransactionSerializer, CryptoTransactionCreateSerializer,
    CryptoAddressSerializer, FiatPlatformSerializer,
    UserFiatAccountSerializer, UserFiatAccountCreateSerializer,
    CryptoComplianceFlagSerializer, CryptoAuditLogSerializer
)
from .services.compliance_service import CryptoComplianceService


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


class CryptoWalletViewSet(viewsets.ModelViewSet):
    """ViewSet for user crypto wallets"""
    serializer_class = CryptoWalletSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return CryptoWallet.objects.filter(user=self.request.user, is_active=True)
    
    def perform_create(self, serializer):
        wallet = serializer.save(user=self.request.user)
        
        # Log wallet creation
        CryptoAuditLog.objects.create(
            user=self.request.user,
            action='wallet_created',
            wallet=wallet,
            details={
                'asset': wallet.asset.symbol,
                'address': wallet.wallet_address
            }
        )
    
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
                'compliance_status': wallet.compliance_status,
                'requires_compliance_approval': wallet.requires_compliance_approval,
                'allocation': (wallet.balance_usd / total_balance_usd * 100) if total_balance_usd > 0 else 0
            })
        
        return Response({
            'total_balance_usd': total_balance_usd,
            'wallet_count': wallets.count(),
            'wallets_requiring_compliance': wallets.filter(requires_compliance_approval=True).count(),
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
        
        # Create audit log
        CryptoAuditLog.objects.create(
            user=self.request.user,
            action='transaction_created',
            transaction=transaction,
            details={
                'type': transaction.transaction_type,
                'amount': str(transaction.amount),
                'asset': transaction.asset.symbol
            }
        )
        
        # Check if transaction requires compliance
        if transaction.requires_compliance_approval:
            # Auto-flag high-value transactions for compliance
            if transaction.is_high_value:
                # Request KYC for high-value transactions
                result = CryptoComplianceService.request_kyc_for_transaction(
                    transaction_id=transaction.id,
                    user_id=self.request.user.id,
                    amount=transaction.amount_usd or transaction.amount,
                    currency='USD',
                    reason=f'High-value crypto transaction: {transaction.amount} {transaction.asset.symbol}'
                )
                
                if result['success']:
                    transaction.compliance_reference = result['compliance_reference']
                    transaction.compliance_status = 'pending'
                    transaction.save()
                    
                    # Create compliance flag
                    CryptoComplianceFlag.objects.create(
                        transaction=transaction,
                        flag_type='high_value',
                        priority='high',
                        description=f'High-value transaction: ${transaction.amount_usd}',
                        indicators={'amount_usd': float(transaction.amount_usd or 0)}
                    )
        
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
        
        # Check if compliance approval is required and not yet obtained
        if transaction.requires_compliance_approval and transaction.compliance_status != 'approved':
            return Response(
                {"error": "Compliance approval required before confirming transaction"},
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
        
        # Create audit log
        CryptoAuditLog.objects.create(
            user=request.user,
            action='transaction_updated',
            transaction=transaction,
            details={'new_status': 'completed'}
        )
        
        return Response({"message": "Transaction confirmed successfully"})
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get transaction statistics"""
        transactions = self.get_queryset()
        
        total_count = transactions.count()
        completed = transactions.filter(status='completed').count()
        pending = transactions.filter(status='pending').count()
        pending_compliance = transactions.filter(status='pending_compliance').count()
        
        total_volume = transactions.filter(status='completed').aggregate(
            total=Sum('amount_usd')
        )['total'] or 0
        
        return Response({
            'total_transactions': total_count,
            'completed': completed,
            'pending': pending,
            'pending_compliance': pending_compliance,
            'total_volume_usd': total_volume
        })
    
    @action(detail=True, methods=['get'])
    def compliance_info(self, request, pk=None):
        """Get compliance information for transaction"""
        transaction = self.get_object()
        
        if not transaction.compliance_reference:
            return Response({'compliance_required': False})
        
        # Get compliance status from central system
        status_data = CryptoComplianceService.check_compliance_status(
            transaction.compliance_reference
        )
        
        # Get compliance flags
        flags = CryptoComplianceFlag.objects.filter(transaction=transaction)
        
        return Response({
            'compliance_required': True,
            'compliance_reference': transaction.compliance_reference,
            'compliance_status': transaction.compliance_status,
            'compliance_flags': CryptoComplianceFlagSerializer(flags, many=True).data,
            'central_compliance_status': status_data
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


class CryptoComplianceFlagViewSet(viewsets.ModelViewSet):
    """ViewSet for crypto compliance flags"""
    serializer_class = CryptoComplianceFlagSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return CryptoComplianceFlag.objects.filter(
            transaction__user=self.request.user
        ).select_related('transaction')
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve a compliance flag"""
        flag = self.get_object()
        
        if flag.is_resolved:
            return Response({'error': 'Flag already resolved'}, status=400)
        
        resolution_notes = request.data.get('resolution_notes', '')
        
        flag.is_resolved = True
        flag.resolved_at = timezone.now()
        flag.resolved_by = request.user
        flag.resolution_notes = resolution_notes
        flag.save()
        
        # Create audit log
        CryptoAuditLog.objects.create(
            user=request.user,
            action='flag_resolved',
            transaction=flag.transaction,
            details={
                'flag_id': str(flag.id),
                'resolution_notes': resolution_notes
            }
        )
        
        return Response({'success': True, 'message': 'Flag resolved'})


class CryptoAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for crypto audit logs"""
    serializer_class = CryptoAuditLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return CryptoAuditLog.objects.filter(user=self.request.user).order_by('-created_at')