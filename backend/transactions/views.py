from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.paginator import Paginator
from django.db.models import Sum, Q, Count
from datetime import datetime, timedelta
from decimal import Decimal
from transactions.models import Wallet, Transaction
from transactions.services import WalletService, InsufficientFundsError
from utils.pusher import trigger_notification  #  ADDED

def index(request):
    return HttpResponse("Hello, this is the Transactions API endpoint.")

@api_view(['GET'])
@permission_classes([IsAuthenticated])  # ADDED: Security
def get_wallet_balance(request, account_number):
    """
    Get wallet balance for an account
    """
    try:
        # Security check: User can only access their own wallet
        if request.user.account_number != account_number:
            return Response(
                {'error': 'Unauthorized access'},
                status=status.HTTP_403_FORBIDDEN
            )

        balance = WalletService.get_balance(account_number)
        return Response({
            'account_number': account_number,
            'balance': str(balance),
            'currency': 'USD'
        })
    except Wallet.DoesNotExist:
        return Response(
            {'error': f'Wallet not found for account {account_number}'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])  # ADDED: Security
def credit_wallet(request):
    """
    Credit wallet (add money) - used by Payments app
    """
    try:
        account_number = request.data.get('account_number')
        amount = Decimal(str(request.data.get('amount', 0)))
        reference = request.data.get('reference', '')
        description = request.data.get('description', '')

        if not account_number or amount <= 0:
            return Response(
                {'error': 'Valid account_number and amount > 0 required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_balance = WalletService.credit_wallet(account_number, amount, reference, description)
        
        #  ADDED: Trigger Pusher event for wallet credit
        trigger_notification(
            account_number=account_number,
            event_name='wallet.credited',
            data={
                'amount': float(amount),
                'new_balance': float(new_balance),
                'reference': reference,
                'description': description,
                'timestamp': datetime.now().isoformat()
            }
        )

        return Response({
            'message': 'Wallet credited successfully',
            'account_number': account_number,
            'amount_added': str(amount),
            'new_balance': str(new_balance),
            'reference': reference,
            'timestamp': datetime.now().isoformat()
        })

    except Wallet.DoesNotExist:
        return Response(
            {'error': f'Wallet not found for account {account_number}'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])  # ADDED: Security
def debit_wallet(request):
    """
    Debit wallet (remove money) - used by Transfers app
    """
    try:
        account_number = request.data.get('account_number')
        amount = Decimal(str(request.data.get('amount', 0)))
        reference = request.data.get('reference', '')
        description = request.data.get('description', '')

        if not account_number or amount <= 0:
            return Response(
                {'error': 'Valid account_number and amount > 0 required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_balance = WalletService.debit_wallet(account_number, amount, reference, description)
        
        #  ADDED: Trigger Pusher event for wallet debit
        trigger_notification(
            account_number=account_number,
            event_name='wallet.debited',
            data={
                'amount': float(amount),
                'new_balance': float(new_balance),
                'reference': reference,
                'description': description,
                'timestamp': datetime.now().isoformat()
            }
        )

        return Response({
            'message': 'Wallet debited successfully',
            'account_number': account_number,
            'amount_deducted': str(amount),
            'new_balance': str(new_balance),
            'reference': reference,
            'timestamp': datetime.now().isoformat()
        })

    except InsufficientFundsError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Wallet.DoesNotExist:
        return Response(
            {'error': f'Wallet not found for account {account_number}'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])  # ADDED: Security
def get_transaction_history(request, account_number):
    """
    Get transaction history for an account
    """
    try:
        # Security check: User can only access their own history
        if request.user.account_number != account_number:
            return Response(
                {'error': 'Unauthorized access'},
                status=status.HTTP_403_FORBIDDEN
            )

        limit = int(request.GET.get('limit', 50))
        transactions = WalletService.get_transaction_history(account_number, limit)

        # Convert to serializable format
        transaction_list = []
        for tx in transactions:
            transaction_list.append({
                'id': str(tx.id),
                'transaction_type': tx.transaction_type,
                'amount': str(tx.amount),
                'reference': tx.reference,
                'description': tx.description,
                'balance_before': str(tx.balance_before),
                'balance_after': str(tx.balance_after),
                'timestamp': tx.timestamp.isoformat(),
                'metadata': tx.metadata
            })

        return Response({
            'account_number': account_number,
            'transactions': transaction_list,
            'count': len(transaction_list)
        })

    except Wallet.DoesNotExist:
        return Response(
            {'error': f'Wallet not found for account {account_number}'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

def get_client_ip(request):
    """
    Get the client's IP address from the request
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# ===== NEW FUNCTIONS FOR FRONTEND DASHBOARD =====

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_wallet_balance_for_current_user(request):
    """Get wallet balance for the current user (authenticated)"""
    try:
        user = request.user
        wallet = Wallet.objects.get(account=user)
        return Response({
            "balance": float(wallet.balance),
            "currency": wallet.currency,
            "account_number": user.account_number
        })
    except Wallet.DoesNotExist:
        return Response({
            "balance": 0,
            "currency": "USD",
            "account_number": user.account_number,
            "message": "No wallet found"
        })
    except Exception as e:
        return Response({
            "error": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recent_transactions(request):
    """Get recent transactions for the current user"""
    try:
        user = request.user
        wallet = Wallet.objects.get(account=user)
        limit = int(request.GET.get("limit", 10))

        transactions = Transaction.objects.filter(
            wallet=wallet
        ).order_by("-timestamp")[:limit]

        transaction_list = []
        for tx in transactions:
            transaction_list.append({
                "id": tx.id,
                "transaction_type": tx.transaction_type,
                "amount": float(tx.amount),
                "currency": wallet.currency,
                "created_at": tx.timestamp.isoformat(),
                "description": tx.description,
                "status": "completed",
                "reference": tx.reference or f"TX-{tx.id}",
            })

        return Response({
            "account_number": user.account_number,
            "transactions": transaction_list,
            "count": len(transaction_list),
        })

    except Wallet.DoesNotExist:
        return Response({
            "account_number": user.account_number,
            "transactions": [],
            "count": 0,
            "message": "No wallet found"
        })
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics for the current user"""
    try:
        user = request.user
        wallet = Wallet.objects.get(account=user)

        # Get ALL transactions (not sliced)
        all_txs = Transaction.objects.filter(wallet=wallet)

        # FIXED: Now matches new transaction types ('credit', 'debit')
        income = all_txs.filter(
            transaction_type="credit"
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        expenses = all_txs.filter(
            transaction_type="debit"
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        return Response({
            "total_balance": float(wallet.balance),
            "total_income": float(income),
            "total_expenses": float(expenses),
            "currency": wallet.currency,
        })

    except Wallet.DoesNotExist:
        return Response({
            "total_balance": 0,
            "total_income": 0,
            "total_expenses": 0,
            "currency": "USD",
            "message": "No wallet found"
        })
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )