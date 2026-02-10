# notifications/views.py - PERMANENT FIX
"""
🎯 NOTIFICATION VIEWS - API endpoints
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Q

from .models import Notification, NotificationPreference, NotificationLog
from .serializers import (
    NotificationSerializer,
    AdminNotificationSerializer,
    NotificationPreferencesSerializer,
    NotificationLogSerializer
)
from .services import NotificationService

class IsAdminUser(permissions.BasePermission):
    """Check if user is admin"""
    def has_permission(self, request, view):
        return request.user and request.user.is_staff

class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet for notifications"""
    serializer_class = NotificationSerializer

    def get_queryset(self):
        """Return notifications for the current user"""
        user = self.request.user
        if user.is_staff:
            # Admin sees all notifications
            return Notification.objects.all().order_by('-created_at')
        else:
            # Regular users see only their notifications
            return Notification.objects.filter(recipient=user).order_by('-created_at')

    def get_serializer_class(self):
        """Use different serializer for admin"""
        if self.request.user.is_staff:
            return AdminNotificationSerializer
        return NotificationSerializer

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a notification as read"""
        notification = self.get_object()

        # Check permission
        if not request.user.is_staff and notification.recipient != request.user:
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )

        success = NotificationService.mark_as_read(pk, request.user)

        if success:
            return Response({'status': 'marked as read'})
        else:
            return Response(
                {'error': 'Failed to mark as read'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread notifications"""
        notifications = self.get_queryset().filter(status='UNREAD')
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)

class UnreadCountView(APIView):
    """Get count of unread notifications - FIXED VERSION"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Return count of unread notifications for current user"""
        # ✅ FIXED: Direct queryset instead of calling NotificationService
        count = Notification.objects.filter(
            recipient=request.user,  # Use the user object directly
            status='UNREAD'
        ).count()
        
        return Response({'unread_count': count})

class MarkAsReadView(APIView):
    """Mark a notification as read"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        success = NotificationService.mark_as_read(pk, request.user)

        if success:
            return Response({'status': 'marked as read'})
        else:
            return Response(
                {'error': 'Failed to mark as read'},
                status=status.HTTP_400_BAD_REQUEST
            )

class MarkAllAsReadView(APIView):
    """Mark all notifications as read"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        notifications = Notification.objects.filter(
            recipient=request.user,
            status='UNREAD'
        )

        count = notifications.count()
        notifications.update(status='READ', read_at=timezone.now())

        return Response({
            'status': f'marked {count} notifications as read'
        })

class AdminAlertsView(APIView):
    """Get admin notifications requiring action"""
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def get(self, request):
        alerts = Notification.get_admin_alerts()
        serializer = AdminNotificationSerializer(alerts, many=True)
        return Response(serializer.data)

class AdminActionRequiredView(APIView):
    """Get count of notifications requiring admin action"""
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def get(self, request):
        count = Notification.objects.filter(
            notification_type__in=[
                'ADMIN_TAC_REQUIRED',
                'ADMIN_SETTLEMENT_REQUIRED',
                'ADMIN_KYC_REVIEW_REQUIRED',
                'ADMIN_NEW_TRANSFER'
            ],
            status='UNREAD'
        ).count()

        return Response({'action_required_count': count})

class NotificationPreferencesView(APIView):
    """Get or update notification preferences"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            preferences = NotificationPreference.objects.get(account=request.user)
            serializer = NotificationPreferencesSerializer(preferences)
            return Response(serializer.data)
        except NotificationPreference.DoesNotExist:
            # Create default preferences
            preferences = NotificationPreference.objects.create(account=request.user)
            serializer = NotificationPreferencesSerializer(preferences)
            return Response(serializer.data)

    def put(self, request):
        try:
            preferences = NotificationPreference.objects.get(account=request.user)
            serializer = NotificationPreferencesSerializer(preferences, data=request.data)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        except NotificationPreference.DoesNotExist:
            return Response(
                {'error': 'Preferences not found'},
                status=status.HTTP_404_NOT_FOUND
            )