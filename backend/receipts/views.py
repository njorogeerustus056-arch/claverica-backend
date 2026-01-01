from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from .models import Receipt
from .serializers import ReceiptSerializer, ReceiptUploadSerializer, ReceiptUpdateSerializer


# ------------------------------
# Upload a receipt
# ------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_receipt_view(request):
    """
    Handles file upload and creates a Receipt record.
    """
    serializer = ReceiptUploadSerializer(data=request.data, context={'request': request})
    if not serializer.is_valid():
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    receipt = serializer.save()
    
    return Response({
        "message": "Upload successful",
        "receipt": ReceiptSerializer(receipt).data
    }, status=status.HTTP_201_CREATED)


# ------------------------------
# List receipts with pagination
# ------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_receipts_view(request):
    receipts = Receipt.objects.filter(user=request.user)
    
    # Filters
    category = request.GET.get('category')
    status_filter = request.GET.get('status')
    search = request.GET.get('search')
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 10))
    
    if category:
        receipts = receipts.filter(category=category)
    if status_filter:
        receipts = receipts.filter(status=status_filter)
    if search:
        receipts = receipts.filter(
            Q(original_file_name__icontains=search) |
            Q(merchant_name__icontains=search) |
            Q(notes__icontains=search)
        )

    paginator = Paginator(receipts, page_size)
    page_obj = paginator.get_page(page)
    serializer = ReceiptSerializer(page_obj, many=True)

    return Response({
        "receipts": serializer.data,
        "pagination": {
            "total": paginator.count,
            "pages": paginator.num_pages,
            "current_page": page,
            "page_size": page_size,
            "has_next": page_obj.has_next(),
            "has_previous": page_obj.has_previous(),
        }
    })


# ------------------------------
# Get receipt detail
# ------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_receipt_detail_view(request, receipt_id):
    try:
        receipt = Receipt.objects.get(id=receipt_id, user=request.user)
        serializer = ReceiptSerializer(receipt)
        return Response({"receipt": serializer.data})
    except Receipt.DoesNotExist:
        return Response({"error": "Receipt not found"}, status=status.HTTP_404_NOT_FOUND)


# ------------------------------
# Update receipt metadata
# ------------------------------
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_receipt_view(request, receipt_id):
    try:
        receipt = Receipt.objects.get(id=receipt_id, user=request.user)
        serializer = ReceiptUpdateSerializer(receipt, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Receipt updated successfully",
                "receipt": ReceiptSerializer(receipt).data
            })
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    except Receipt.DoesNotExist:
        return Response({"error": "Receipt not found"}, status=status.HTTP_404_NOT_FOUND)


# ------------------------------
# Delete a receipt
# ------------------------------
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_receipt_view(request, receipt_id):
    try:
        receipt = Receipt.objects.get(id=receipt_id, user=request.user)
        if receipt.file:
            receipt.file.delete()  # deletes the actual file from storage
        receipt.delete()
        return Response({"message": "Receipt deleted successfully"})
    except Receipt.DoesNotExist:
        return Response({"error": "Receipt not found"}, status=status.HTTP_404_NOT_FOUND)


# ------------------------------
# Get receipt stats
# ------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_receipt_stats_view(request):
    receipts = Receipt.objects.filter(user=request.user)

    total_receipts = receipts.count()
    total_amount = receipts.aggregate(total=Sum('amount'))['total'] or 0

    # Category stats
    category_stats = {}
    for category, _ in Receipt.CATEGORY_CHOICES:
        cat_receipts = receipts.filter(category=category)
        count = cat_receipts.count()
        amount = cat_receipts.aggregate(total=Sum('amount'))['total'] or 0
        if count > 0:
            category_stats[category] = {
                "count": count, 
                "total_amount": float(amount)
            }

    # Status stats
    status_stats = {}
    for status_choice, _ in Receipt.STATUS_CHOICES:
        count = receipts.filter(status=status_choice).count()
        if count > 0:
            status_stats[status_choice] = count

    # Monthly stats (last 6 months)
    from django.utils import timezone
    from datetime import timedelta
    
    monthly_stats = []
    for i in range(5, -1, -1):
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_start = month_start - timedelta(days=30*i)
        month_end = month_start + timedelta(days=30)
        
        month_receipts = receipts.filter(
            uploaded_at__gte=month_start,
            uploaded_at__lt=month_end
        )
        month_count = month_receipts.count()
        month_amount = month_receipts.aggregate(total=Sum('amount'))['total'] or 0
        
        monthly_stats.append({
            "month": month_start.strftime("%Y-%m"),
            "count": month_count,
            "total_amount": float(month_amount)
        })

    return Response({
        "total_receipts": total_receipts,
        "total_amount": float(total_amount),
        "currency": "USD",
        "categories": category_stats,
        "status_breakdown": status_stats,
        "monthly_stats": monthly_stats
    })