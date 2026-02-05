"""
payments/views.py - API views for payments
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404

from .models import Payment, PaymentCode
from .serializers import (
    PaymentSerializer, PaymentCodeSerializer,
    ProcessPaymentSerializer, AssignPaymentCodeSerializer
)
from .services import PaymentService
from accounts.models import Account


class PaymentCodeViewSet(viewsets.ModelViewSet):
    """ViewSet for PaymentCode (Admin only)"""
    queryset = PaymentCode.objects.all()
    serializer_class = PaymentCodeSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'code'

    def get_queryset(self):
        """Filter queryset based on permissions"""
        if self.request.user.is_superuser:
            return PaymentCode.objects.all()
        return PaymentCode.objects.none()  # Only admin can access

    @action(detail=False, methods=['post'])
    def assign(self, request):
        """Assign payment code to account"""
        serializer = AssignPaymentCodeSerializer(data=request.data)
        if serializer.is_valid():
            try:
                account = Account.objects.get(
                    account_number=serializer.validated_data['account_number']
                )
                payment_code = PaymentService.assign_payment_code(
                    account=account,
                    code=serializer.validated_data['code']
                )
                return Response(
                    PaymentCodeSerializer(payment_code).data,
                    status=status.HTTP_201_CREATED
                )
            except Account.DoesNotExist:
                return Response(
                    {"error": "Account not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            except Exception as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaymentViewSet(viewsets.ModelViewSet):
    """ViewSet for Payment"""
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]  # CHANGED: Allow authenticated users

    def get_queryset(self):
        """Filter payments based on user role"""
        user = self.request.user

        if user.is_superuser:
            # Admin sees all payments
            return Payment.objects.all()
        elif hasattr(user, 'account'):
            # Regular users see only their payments
            return Payment.objects.filter(account=user.account).order_by('-created_at')

        return Payment.objects.none()

    def list(self, request, *args, **kwargs):
        """Override list to handle user permissions gracefully"""
        queryset = self.filter_queryset(self.get_queryset())
        
        # For regular users, show limited info
        if not request.user.is_superuser:
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        
        # Admin gets full list
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=['post'])
    def process(self, request):
        """Process a new payment (Admin only)"""
        if not request.user.is_superuser:
            return Response(
                {"error": "Only admin can process payments"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ProcessPaymentSerializer(data=request.data)
        if serializer.is_valid():
            try:
                payment = PaymentService.process_payment(
                    payment_code=serializer.validated_data['payment_code'],
                    amount=serializer.validated_data['amount'],
                    sender=serializer.validated_data['sender'],
                    description=serializer.validated_data.get('description', '')
                )

                return Response(
                    PaymentSerializer(payment).data,
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get payment history for current user"""
        if not hasattr(request.user, 'account'):
            return Response(
                {"error": "User has no account"},
                status=status.HTTP_400_BAD_REQUEST
            )

        limit = int(request.GET.get('limit', 50))
        payments = PaymentService.get_payment_history(
            account_number=request.user.account.account_number,
            limit=limit
        )
        
        serializer = PaymentSerializer(payments, many=True)
        return Response({
            'account_number': request.user.account.account_number,
            'count': len(payments),
            'payments': serializer.data
        })

    @action(detail=True, methods=['post'])
    def resend_notification(self, request, pk=None):
        """Resend payment notification (Admin only)"""
        if not request.user.is_superuser:
            return Response(
                {"error": "Only admin can resend notifications"},
                status=status.HTTP_403_FORBIDDEN
            )

        payment = self.get_object()
        success = PaymentService.send_payment_notification(payment)

        if success:
            return Response({"message": "Notification resent successfully"})
        return Response(
            {"error": "Failed to resend notification"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )