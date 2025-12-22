from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
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
            "stats": "/api/escrow/stats/"
        }
    })


@api_view(['POST'])
def create_escrow_view(request):
    serializer = EscrowCreateSerializer(data=request.data)
    if serializer.is_valid():
        escrow = serializer.save()
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
            "escrow": EscrowSerializer(escrow).data
        }, status=status.HTTP_201_CREATED)
    return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def list_escrows_view(request):
    user_id = request.GET.get('user_id')
    if not user_id:
        return Response({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    
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
def get_escrow_detail_view(request, escrow_id):
    try:
        escrow = Escrow.objects.get(id=escrow_id)
        user_id = request.GET.get('user_id', 'anonymous')
        EscrowLog.objects.create(
            escrow=escrow,
            user_id=user_id,
            user_name=request.GET.get('user_name', 'Anonymous'),
            action='viewed',
            details=f"Viewed escrow {escrow.escrow_id}",
            ip_address=get_client_ip(request)
        )
        serializer = EscrowSerializer(escrow)
        return Response({"escrow": serializer.data})
    except Escrow.DoesNotExist:
        return Response({"error": "Escrow not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PATCH'])
def update_escrow_view(request, escrow_id):
    try:
        escrow = Escrow.objects.get(id=escrow_id)
        serializer = EscrowUpdateSerializer(escrow, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            user_id = request.data.get('user_id', 'anonymous')
            EscrowLog.objects.create(
                escrow=escrow,
                user_id=user_id,
                user_name=request.data.get('user_name', 'Anonymous'),
                action='updated',
                details=f"Updated escrow {escrow.escrow_id}",
                ip_address=get_client_ip(request)
            )
            return Response({"message": "Escrow updated successfully", "escrow": EscrowSerializer(escrow).data})
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    except Escrow.DoesNotExist:
        return Response({"error": "Escrow not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def fund_escrow_view(request, escrow_id):
    try:
        escrow = Escrow.objects.get(id=escrow_id)
        if escrow.status != 'pending':
            return Response({"error": "Escrow can only be funded when status is pending"}, status=status.HTTP_400_BAD_REQUEST)
        escrow.status = 'funded'
        escrow.funded_at = datetime.now()
        escrow.save()
        user_id = request.data.get('user_id', escrow.sender_id)
        EscrowLog.objects.create(
            escrow=escrow,
            user_id=user_id,
            user_name=request.data.get('user_name', escrow.sender_name),
            action='funded',
            details=f"Funded escrow {escrow.escrow_id} with ${escrow.total_amount}",
            ip_address=get_client_ip(request)
        )
        return Response({"message": "Escrow funded successfully", "escrow": EscrowSerializer(escrow).data})
    except Escrow.DoesNotExist:
        return Response({"error": "Escrow not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def release_escrow_view(request, escrow_id):
    try:
        escrow = Escrow.objects.get(id=escrow_id)
        user_id = request.data.get('user_id')
        if not escrow.can_release():
            return Response({"error": "Escrow cannot be released at this time"}, status=status.HTTP_400_BAD_REQUEST)
        if user_id == escrow.sender_id:
            escrow.release_approved_by_sender = True
        elif user_id == escrow.receiver_id:
            escrow.release_approved_by_receiver = True
        else:
            return Response({"error": "Unauthorized to release this escrow"}, status=status.HTTP_403_FORBIDDEN)
        if escrow.release_approved_by_sender:
            success = escrow.release()
            if success:
                EscrowLog.objects.create(
                    escrow=escrow,
                    user_id=user_id,
                    user_name=request.data.get('user_name', 'User'),
                    action='released',
                    details=f"Released escrow {escrow.escrow_id}",
                    ip_address=get_client_ip(request)
                )
                return Response({"message": "Escrow released successfully", "escrow": EscrowSerializer(escrow).data})
        else:
            escrow.save()
            return Response({"message": "Release approval recorded", "escrow": EscrowSerializer(escrow).data})
    except Escrow.DoesNotExist:
        return Response({"error": "Escrow not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def dispute_escrow_view(request, escrow_id):
    try:
        escrow = Escrow.objects.get(id=escrow_id)
        user_id = request.data.get('user_id')
        reason = request.data.get('reason', '')
        if escrow.status not in ['funded', 'pending']:
            return Response({"error": "Cannot dispute escrow with current status"}, status=status.HTTP_400_BAD_REQUEST)
        escrow.dispute_status = 'opened'
        escrow.dispute_reason = reason
        escrow.dispute_opened_by = user_id
        escrow.dispute_opened_at = datetime.now()
        escrow.status = 'disputed'
        escrow.save()
        EscrowLog.objects.create(
            escrow=escrow,
            user_id=user_id,
            user_name=request.data.get('user_name', 'User'),
            action='disputed',
            details=f"Opened dispute for escrow {escrow.escrow_id}: {reason}",
            ip_address=get_client_ip(request)
        )
        return Response({"message": "Dispute opened successfully", "escrow": EscrowSerializer(escrow).data})
    except Escrow.DoesNotExist:
        return Response({"error": "Escrow not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def get_escrow_stats_view(request):
    user_id = request.GET.get('user_id')
    if not user_id:
        return Response({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    escrows = Escrow.objects.filter(Q(sender_id=user_id) | Q(receiver_id=user_id))
    total_escrows = escrows.count()
    active_escrows = escrows.filter(status__in=['pending', 'funded']).count()
    completed_escrows = escrows.filter(status='released').count()
    pending_disputes = escrows.filter(dispute_status__in=['opened', 'under_review']).count()
    total_amount_in_escrow = escrows.filter(status__in=['pending', 'funded']).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    total_amount_released = escrows.filter(status='released').aggregate(total=Sum('amount'))['total'] or Decimal('0')
    return Response({
        "total_escrows": total_escrows,
        "active_escrows": active_escrows,
        "completed_escrows": completed_escrows,
        "total_amount_in_escrow": float(total_amount_in_escrow),
        "total_amount_released": float(total_amount_released),
        "pending_disputes": pending_disputes,
        "currency": "USD"
    })


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
