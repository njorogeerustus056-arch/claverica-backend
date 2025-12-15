from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from backend.supabase_storage import upload_receipt, list_user_receipts, generate_signed_url, delete_receipt_file
from .models import Receipt
from .serializers import ReceiptSerializer, ReceiptUploadSerializer, ReceiptUpdateSerializer
import os
from datetime import datetime
from django.core.paginator import Paginator


@csrf_exempt
@api_view(['POST'])
def upload_receipt_view(request):
    """
    Handles file upload from user and sends it to Supabase Storage.
    Also creates a database record for the receipt.
    """
    serializer = ReceiptUploadSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    user_id = serializer.validated_data['user_id']
    file = serializer.validated_data['file']
    
    # Save file temporarily
    temp_path = f"/tmp/{file.name}"
    with open(temp_path, "wb+") as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    
    try:
        # Upload to Supabase
        storage_path = upload_receipt(user_id, temp_path, file.name)
        
        # Create database record
        receipt = Receipt.objects.create(
            user_id=user_id,
            file_name=file.name,
            original_file_name=file.name,
            file_size=file.size,
            file_type=file.content_type,
            storage_path=storage_path,
            merchant_name=serializer.validated_data.get('merchant_name', ''),
            amount=serializer.validated_data.get('amount'),
            currency=serializer.validated_data.get('currency', 'USD'),
            transaction_date=serializer.validated_data.get('transaction_date'),
            category=serializer.validated_data.get('category', 'other'),
            notes=serializer.validated_data.get('notes', ''),
            tags=serializer.validated_data.get('tags', []),
        )
        
        # Clean up temp file
        os.remove(temp_path)
        
        receipt_data = ReceiptSerializer(receipt).data
        return Response({
            "message": "Upload successful",
            "receipt": receipt_data
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def list_receipts_view(request):
    """
    Lists all receipts for a given user with pagination and filtering.
    """
    user_id = request.GET.get("user_id")
    if not user_id:
        return Response({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Get query parameters
    category = request.GET.get('category')
    status_filter = request.GET.get('status')
    search = request.GET.get('search')
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 10))
    
    # Build query
    receipts = Receipt.objects.filter(user_id=user_id)
    
    if category:
        receipts = receipts.filter(category=category)
    if status_filter:
        receipts = receipts.filter(status=status_filter)
    if search:
        receipts = receipts.filter(
            original_file_name__icontains=search
        ) | receipts.filter(
            merchant_name__icontains=search
        )
    
    # Pagination
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


@api_view(['GET'])
def get_receipt_detail_view(request, receipt_id):
    """
    Get details of a specific receipt.
    """
    try:
        receipt = Receipt.objects.get(id=receipt_id)
        serializer = ReceiptSerializer(receipt)
        return Response({"receipt": serializer.data})
    except Receipt.DoesNotExist:
        return Response({"error": "Receipt not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PATCH'])
def update_receipt_view(request, receipt_id):
    """
    Update receipt metadata.
    """
    try:
        receipt = Receipt.objects.get(id=receipt_id)
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


@api_view(['DELETE'])
def delete_receipt_view(request, receipt_id):
    """
    Delete a receipt and its file from storage.
    """
    try:
        receipt = Receipt.objects.get(id=receipt_id)
        
        # Delete from Supabase storage
        try:
            delete_receipt_file(receipt.user_id, receipt.file_name)
        except Exception as e:
            print(f"Warning: Could not delete file from storage: {e}")
        
        # Delete database record
        receipt.delete()
        
        return Response({"message": "Receipt deleted successfully"})
        
    except Receipt.DoesNotExist:
        return Response({"error": "Receipt not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def get_signed_url_view(request):
    """
    Returns a signed URL for downloading a receipt.
    """
    user_id = request.GET.get("user_id")
    receipt_id = request.GET.get("receipt_id")
    
    if not user_id or not receipt_id:
        return Response(
            {"error": "user_id and receipt_id are required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        receipt = Receipt.objects.get(id=receipt_id, user_id=user_id)
        url = generate_signed_url(user_id, receipt.file_name)
        return Response({"signed_url": url})
    except Receipt.DoesNotExist:
        return Response({"error": "Receipt not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_receipt_stats_view(request):
    """
    Get receipt statistics for a user.
    """
    user_id = request.GET.get("user_id")
    if not user_id:
        return Response({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    receipts = Receipt.objects.filter(user_id=user_id)
    
    # Calculate stats
    total_receipts = receipts.count()
    total_amount = sum([r.amount for r in receipts if r.amount]) or 0
    
    # Category breakdown
    category_stats = {}
    for category, _ in Receipt.CATEGORY_CHOICES:
        count = receipts.filter(category=category).count()
        amount = sum([r.amount for r in receipts.filter(category=category) if r.amount]) or 0
        if count > 0:
            category_stats[category] = {
                "count": count,
                "total_amount": float(amount)
            }
    
    # Status breakdown
    status_stats = {}
    for status_choice, _ in Receipt.STATUS_CHOICES:
        count = receipts.filter(status=status_choice).count()
        if count > 0:
            status_stats[status_choice] = count
    
    return Response({
        "total_receipts": total_receipts,
        "total_amount": float(total_amount),
        "currency": "USD",
        "categories": category_stats,
        "status_breakdown": status_stats,
    })
