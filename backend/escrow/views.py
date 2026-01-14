# escrow/views.py - UPDATED FOR COMPLIANCE AWARENESS

from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from django.core.paginator import Paginator
from django.db.models import Sum, Q, Count
from .models import Escrow, EscrowLog
from .serializers import (
    EscrowSerializer, 
    EscrowCreateSerializer,
    EscrowUpdateSerializer,
    EscrowLogSerializer
)
from datetime import datetime
from decimal import Decimal


def index(request):
    """Base escrow API endpoint"""
    return JsonResponse({
        "message": "ClaveRica Escrow API is working!",
        "version": "1.0.0",
        "endpoints": {
            "create": "/api/escrow/create/",
            "list": "/api/escrow/list/",
            "detail": "/api/escrow/<escrow_id>/",
            "stats": "/api/escrow/stats/",
            "compliance": {  # NEW: Added compliance endpoints
                "dispute": "/api/escrow/<escrow_id>/compliance/dispute/",
                "kyc": "/api/escrow/<escrow_id>/compliance/kyc/",
                "status": "/api/escrow/<escrow_id>/compliance/status/"
            }
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_escrow_view(request):
    """Create a new escrow"""
    serializer = EscrowCreateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        escrow = serializer.save()
        
        # NEW: Check if high-value escrow requires compliance
        if escrow.amount > Decimal('10000'):
            escrow.requires_compliance_approval = True
            escrow.save()
        
        EscrowLog.objects.create(
            escrow=escrow,
            user_id=escrow.sender_id,
            user_name=escrow.sender_name,
            action='created',
            details=f"Created escrow {escrow.escrow_id}",
            ip_address=get_client_ip(request)
        )
        return Response({
            "message": "Escrow created successfully",
            "escrow": EscrowSerializer(escrow).data,
            "requires_compliance": escrow.requires_compliance_approval  # NEW
        }, status=status.HTTP_201_CREATED)
    return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_escrows_view(request):
    """List escrows for the authenticated user"""
    user_id = request.user.id  # Get user_id from authenticated user
    role = request.GET.get('role', 'all')
    status_filter = request.GET.get('status')
    search = request.GET.get('search')
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 10))
    
    if role == 'sender':
        escrows = Escrow.objects.filter(sender_id=user_id)
    elif role == 'receiver':
        escrows = Escrow.objects.filter(receiver_id=user_id)
    else:
        escrows = Escrow.objects.filter(Q(sender_id=user_id) | Q(receiver_id=user_id))
    
    if status_filter:
        escrows = escrows.filter(status=status_filter)
    if search:
        escrows = escrows.filter(Q(title__icontains=search) | Q(description__icontains=search) | Q(escrow_id__icontains=search))
    
    # Order by most recent first
    escrows = escrows.order_by('-created_at')
    
    paginator = Paginator(escrows, page_size)
    page_obj = paginator.get_page(page)
    serializer = EscrowSerializer(page_obj, many=True)
    
    return Response({
        "escrows": serializer.data,
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
@permission_classes([IsAuthenticated])
def get_escrow_detail_view(request, escrow_id):
    """Get detailed information about a specific escrow"""
    try:
        escrow = Escrow.objects.get(id=escrow_id)
        
        # Check if user is authorized to view this escrow
        user_id = request.user.id
        if escrow.sender_id != user_id and escrow.receiver_id != user_id:
            return Response({"error": "Unauthorized to view this escrow"}, status=status.HTTP_403_FORBIDDEN)
        
        EscrowLog.objects.create(
            escrow=escrow,
            user_id=user_id,
            user_name=request.user.username,
            action='viewed',
            details=f"Viewed escrow {escrow.escrow_id}",
            ip_address=get_client_ip(request)
        )
        serializer = EscrowSerializer(escrow)
        return Response({"escrow": serializer.data})
    except Escrow.DoesNotExist:
        return Response({"error": "Escrow not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_escrow_view(request, escrow_id):
    """Update escrow details"""
    try:
        escrow = Escrow.objects.get(id=escrow_id)
        
        # Check if user is authorized to update this escrow
        user_id = request.user.id
        if escrow.sender_id != user_id:
            return Response({"error": "Only the sender can update this escrow"}, status=status.HTTP_403_FORBIDDEN)
        
        # Prevent updating if escrow is already funded or beyond
        if escrow.status not in ['pending', 'draft']:
            return Response({"error": "Cannot update escrow after funding"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = EscrowUpdateSerializer(escrow, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            EscrowLog.objects.create(
                escrow=escrow,
                user_id=user_id,
                user_name=request.user.username,
                action='updated',
                details=f"Updated escrow {escrow.escrow_id}",
                ip_address=get_client_ip(request)
            )
            return Response({"message": "Escrow updated successfully", "escrow": EscrowSerializer(escrow).data})
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    except Escrow.DoesNotExist:
        return Response({"error": "Escrow not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def fund_escrow_view(request, escrow_id):
    """Fund an escrow"""
    try:
        escrow = Escrow.objects.get(id=escrow_id)
        
        # Check if user is authorized to fund this escrow
        user_id = request.user.id
        if escrow.sender_id != user_id:
            return Response({"error": "Only the sender can fund this escrow"}, status=status.HTTP_403_FORBIDDEN)
        
        if escrow.status != 'pending':
            return Response({"error": "Escrow can only be funded when status is pending"}, status=status.HTTP_400_BAD_REQUEST)
        
        # In a real application, you would integrate with a payment gateway here
        # For now, we'll just update the status
        
        escrow.status = 'funded'
        escrow.funded_at = datetime.now()
        escrow.save()
        
        EscrowLog.objects.create(
            escrow=escrow,
            user_id=user_id,
            user_name=request.user.username,
            action='funded',
            details=f"Funded escrow {escrow.escrow_id} with ${escrow.amount}",
            ip_address=get_client_ip(request)
        )
        return Response({"message": "Escrow funded successfully", "escrow": EscrowSerializer(escrow).data})
    except Escrow.DoesNotExist:
        return Response({"error": "Escrow not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def release_escrow_view(request, escrow_id):
    """Release funds from escrow"""
    try:
        escrow = Escrow.objects.get(id=escrow_id)
        user_id = request.user.id
        
        # Check if user is authorized to release this escrow
        if user_id != escrow.sender_id and user_id != escrow.receiver_id:
            return Response({"error": "Unauthorized to release this escrow"}, status=status.HTTP_403_FORBIDDEN)
        
        if not escrow.can_release():
            return Response({"error": "Escrow cannot be released at this time"}, status=status.HTTP_400_BAD_REQUEST)
        
        if user_id == escrow.sender_id:
            escrow.release_approved_by_sender = True
        elif user_id == escrow.receiver_id:
            escrow.release_approved_by_receiver = True
        
        # Check if both parties have approved the release
        if escrow.release_approved_by_sender and escrow.release_approved_by_receiver:
            success = escrow.release()
            if success:
                EscrowLog.objects.create(
                    escrow=escrow,
                    user_id=user_id,
                    user_name=request.user.username,
                    action='released',
                    details=f"Released escrow {escrow.escrow_id}",
                    ip_address=get_client_ip(request)
                )
                return Response({"message": "Escrow released successfully", "escrow": EscrowSerializer(escrow).data})
            else:
                return Response({"error": "Failed to release escrow"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            escrow.save()
            # Log the approval
            EscrowLog.objects.create(
                escrow=escrow,
                user_id=user_id,
                user_name=request.user.username,
                action='approved_release',
                details=f"Approved release for escrow {escrow.escrow_id}",
                ip_address=get_client_ip(request)
            )
            return Response({"message": "Release approval recorded", "escrow": EscrowSerializer(escrow).data})
    except Escrow.DoesNotExist:
        return Response({"error": "Escrow not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def dispute_escrow_view(request, escrow_id):
    """Open a dispute for an escrow"""
    try:
        escrow = Escrow.objects.get(id=escrow_id)
        user_id = request.user.id
        
        # Check if user is authorized to dispute this escrow
        if user_id != escrow.sender_id and user_id != escrow.receiver_id:
            return Response({"error": "Unauthorized to dispute this escrow"}, status=status.HTTP_403_FORBIDDEN)
        
        reason = request.data.get('reason', '')
        if not reason:
            return Response({"error": "Dispute reason is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        if escrow.status not in ['funded', 'pending']:
            return Response({"error": "Cannot dispute escrow with current status"}, status=status.HTTP_400_BAD_REQUEST)
        
        if escrow.dispute_status == 'opened':
            return Response({"error": "Dispute already opened for this escrow"}, status=status.HTTP_400_BAD_REQUEST)
        
        # NEW: For high-value disputes, mark as requiring compliance
        if escrow.amount > Decimal('5000'):
            escrow.requires_compliance_approval = True
        
        escrow.dispute_status = 'opened'
        escrow.dispute_reason = reason
        escrow.dispute_opened_by = user_id
        escrow.dispute_opened_at = datetime.now()
        escrow.status = 'disputed'
        escrow.save()
        
        EscrowLog.objects.create(
            escrow=escrow,
            user_id=user_id,
            user_name=request.user.username,
            action='disputed',
            details=f"Opened dispute for escrow {escrow.escrow_id}: {reason}",
            ip_address=get_client_ip(request)
        )
        
        response_data = {
            "message": "Dispute opened successfully", 
            "escrow": EscrowSerializer(escrow).data
        }
        
        # NEW: Add compliance note if needed
        if escrow.requires_compliance_approval:
            response_data["compliance_note"] = "This dispute requires compliance review. Please use the compliance endpoint for resolution."
        
        return Response(response_data)
    except Escrow.DoesNotExist:
        return Response({"error": "Escrow not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_escrow_stats_view(request):
    """Get statistics for the authenticated user's escrows"""
    user_id = request.user.id
    escrows = Escrow.objects.filter(Q(sender_id=user_id) | Q(receiver_id=user_id))
    
    total_escrows = escrows.count()
    active_escrows = escrows.filter(status__in=['pending', 'funded']).count()
    completed_escrows = escrows.filter(status='released').count()
    disputed_escrows = escrows.filter(status='disputed').count()
    pending_disputes = escrows.filter(dispute_status__in=['opened', 'under_review']).count()
    
    total_amount_in_escrow = escrows.filter(status__in=['pending', 'funded']).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    total_amount_released = escrows.filter(status='released').aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Additional stats
    sent_escrows = escrows.filter(sender_id=user_id).count()
    received_escrows = escrows.filter(receiver_id=user_id).count()
    
    return Response({
        "total_escrows": total_escrows,
        "active_escrows": active_escrows,
        "completed_escrows": completed_escrows,
        "disputed_escrows": disputed_escrows,
        "total_amount_in_escrow": float(total_amount_in_escrow),
        "total_amount_released": float(total_amount_released),
        "pending_disputes": pending_disputes,
        "sent_escrows": sent_escrows,
        "received_escrows": received_escrows,
        "currency": "USD"
    })


def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip