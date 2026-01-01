from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.core.paginator import Paginator
from django.db.models import Sum, Q, Count
from .models import Transaction, TransactionLog
from .serializers import (
    TransactionSerializer, 
    TransactionCreateSerializer,
    TransactionUpdateSerializer,
    TransactionLogSerializer
)
from datetime import datetime, timedelta
from decimal import Decimal


def index(request):
    return HttpResponse("Hello, this is the Transactions API endpoint.")


@api_view(['POST'])
def create_transaction_view(request):
    """
    Create a new transaction
    """
    serializer = TransactionCreateSerializer(data=request.data)
    
    if serializer.is_valid():
        transaction = serializer.save()
        
        # Create audit log
        TransactionLog.objects.create(
            transaction=transaction,
            user_id=transaction.user_id,
            action='create',
            details=f"Created transaction {transaction.transaction_id}",
            ip_address=get_client_ip(request)
        )
        
        return Response({
            "message": "Transaction created successfully",
            "transaction": TransactionSerializer(transaction).data
        }, status=status.HTTP_201_CREATED)
    
    return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def list_transactions_view(request):
    """
    List all transactions for a user with filtering and pagination
    """
    user_id = request.GET.get('user_id')
    if not user_id:
        return Response({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Get query parameters
    transaction_type = request.GET.get('type')
    status_filter = request.GET.get('status')
    category = request.GET.get('category')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    search = request.GET.get('search')
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 10))
    
    # Build query
    transactions = Transaction.objects.filter(user_id=user_id)
    
    if transaction_type:
        transactions = transactions.filter(type=transaction_type)
    if status_filter:
        transactions = transactions.filter(status=status_filter)
    if category:
        transactions = transactions.filter(category=category)
    if start_date:
        transactions = transactions.filter(transaction_date__gte=start_date)
    if end_date:
        transactions = transactions.filter(transaction_date__lte=end_date)
    if search:
        transactions = transactions.filter(
            Q(merchant__icontains=search) | 
            Q(description__icontains=search) |
            Q(transaction_id__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(transactions, page_size)
    page_obj = paginator.get_page(page)
    
    serializer = TransactionSerializer(page_obj, many=True)
    
    return Response({
        "transactions": serializer.data,
        "pagination": {
            "total": paginator.count,
            "pages": paginator.num_pages,
            "current_page": page,
            "page_size": page_size,
            "has_next": page_obj.has_next(),
            "has_previous": page_obj.has_previous(),
        }
    })


@api_view(['GET'])
def get_transaction_detail_view(request, transaction_id):
    """
    Get details of a specific transaction
    """
    try:
        transaction = Transaction.objects.get(id=transaction_id)
        
        # Create audit log
        TransactionLog.objects.create(
            transaction=transaction,
            user_id=transaction.user_id,
            action='view',
            details=f"Viewed transaction {transaction.transaction_id}",
            ip_address=get_client_ip(request)
        )
        
        serializer = TransactionSerializer(transaction)
        return Response({"transaction": serializer.data})
    except Transaction.DoesNotExist:
        return Response({"error": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PATCH'])
def update_transaction_view(request, transaction_id):
    """
    Update a transaction
    """
    try:
        transaction = Transaction.objects.get(id=transaction_id)
        serializer = TransactionUpdateSerializer(transaction, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            
            # Create audit log
            TransactionLog.objects.create(
                transaction=transaction,
                user_id=transaction.user_id,
                action='update',
                details=f"Updated transaction {transaction.transaction_id}",
                ip_address=get_client_ip(request)
            )
            
            return Response({
                "message": "Transaction updated successfully",
                "transaction": TransactionSerializer(transaction).data
            })
        
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
    except Transaction.DoesNotExist:
        return Response({"error": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
def delete_transaction_view(request, transaction_id):
    """
    Delete a transaction (soft delete by marking as cancelled)
    """
    try:
        transaction = Transaction.objects.get(id=transaction_id)
        
        # Soft delete - mark as cancelled
        transaction.status = 'cancelled'
        transaction.save()
        
        # Create audit log
        TransactionLog.objects.create(
            transaction=transaction,
            user_id=transaction.user_id,
            action='delete',
            details=f"Cancelled transaction {transaction.transaction_id}",
            ip_address=get_client_ip(request)
        )
        
        return Response({"message": "Transaction cancelled successfully"})
        
    except Transaction.DoesNotExist:
        return Response({"error": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def get_transaction_stats_view(request):
    """
    Get transaction statistics for a user
    """
    user_id = request.GET.get('user_id')
    if not user_id:
        return Response({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Get date range (default to last 30 days)
    days = int(request.GET.get('days', 30))
    start_date = datetime.now() - timedelta(days=days)
    
    transactions = Transaction.objects.filter(
        user_id=user_id,
        transaction_date__gte=start_date
    )
    
    # Calculate totals
    total_transactions = transactions.count()
    
    credits = transactions.filter(type='credit', status='completed')
    total_credits = credits.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    debits = transactions.filter(type='debit', status='completed')
    total_debits = debits.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    net_balance = total_credits - total_debits
    
    # Status breakdown
    status_counts = transactions.values('status').annotate(count=Count('id'))
    status_breakdown = {item['status']: item['count'] for item in status_counts}
    
    # Category breakdown
    category_stats = {}
    for category, _ in Transaction.CATEGORY_CHOICES:
        cat_transactions = transactions.filter(category=category, status='completed')
        count = cat_transactions.count()
        amount = cat_transactions.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        if count > 0:
            category_stats[category] = {
                "count": count,
                "total_amount": float(amount)
            }
    
    return Response({
        "total_transactions": total_transactions,
        "total_credits": float(total_credits),
        "total_debits": float(total_debits),
        "net_balance": float(net_balance),
        "currency": "USD",
        "pending_count": status_breakdown.get('pending', 0),
        "completed_count": status_breakdown.get('completed', 0),
        "failed_count": status_breakdown.get('failed', 0),
        "category_breakdown": category_stats,
        "period_days": days
    })


@api_view(['GET'])
def get_recent_activity_view(request):
    """
    Get recent transaction activity for a user
    """
    user_id = request.GET.get('user_id')
    if not user_id:
        return Response({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    limit = int(request.GET.get('limit', 10))
    
    transactions = Transaction.objects.filter(user_id=user_id).order_by('-transaction_date')[:limit]
    serializer = TransactionSerializer(transactions, many=True)
    
    return Response({
        "activities": serializer.data,
        "count": len(serializer.data)
    })


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