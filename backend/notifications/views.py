from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import (
    Notification, NotificationPreference, NotificationTemplate,
    NotificationLog, NotificationDevice
)
from .serializers import (
    NotificationSerializer, NotificationCreateSerializer,
    NotificationPreferenceSerializer, NotificationTemplateSerializer,
    NotificationLogSerializer, NotificationDeviceSerializer,
    NotificationStatsSerializer, BulkNotificationSerializer,
    MarkAsReadSerializer
)
from .pusher_client import trigger_notification  # ✅ Use centralized pusher client


class NotificationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return NotificationCreateSerializer if self.action == 'create' else NotificationSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Notification.objects.filter(user=user)

        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == 'true')

        is_archived = self.request.query_params.get('is_archived')
        if is_archived is not None:
            queryset = queryset.filter(is_archived=is_archived.lower() == 'true')
        else:
            queryset = queryset.filter(is_archived=False)

        notification_type = self.request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)

        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)

        return queryset

    def get_serializer_context(self):
        return {'user': self.request.user}

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.mark_as_read()
        
        # Trigger Pusher update for read status change
        trigger_notification(
            user_id=request.user.id,
            event="notification_updated",
            data={
                "notification_id": str(notification.notification_id),
                "action": "marked_read",
                "is_read": True,
                "read_at": timezone.now().isoformat()
            }
        )
        
        return Response({'status': 'Notification marked as read'})

    @action(detail=True, methods=['post'])
    def mark_as_unread(self, request, pk=None):
        notification = self.get_object()
        notification.mark_as_unread()
        
        # Trigger Pusher update for unread status change
        trigger_notification(
            user_id=request.user.id,
            event="notification_updated",
            data={
                "notification_id": str(notification.notification_id),
                "action": "marked_unread",
                "is_read": False
            }
        )
        
        return Response({'status': 'Notification marked as unread'})

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        notification = self.get_object()
        notification.archive()
        return Response({'status': 'Notification archived'})

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        updated_count = Notification.objects.filter(user=request.user, is_read=False, is_archived=False).update(
            is_read=True, read_at=timezone.now())
        
        # Trigger Pusher event for bulk update
        trigger_notification(
            user_id=request.user.id,
            event="notifications_updated",
            data={
                "action": "all_marked_read",
                "count": updated_count,
                "timestamp": timezone.now().isoformat()
            }
        )
            
        return Response({'status': 'All notifications marked as read', 'count': updated_count})

    @action(detail=False, methods=['post'])
    def mark_multiple_as_read(self, request):
        serializer = MarkAsReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notification_ids = serializer.validated_data.get('notification_ids', [])
        updated_count = Notification.objects.filter(id__in=notification_ids, user=request.user).update(
            is_read=True, read_at=timezone.now())
        
        # Trigger Pusher event for multiple updates
        trigger_notification(
            user_id=request.user.id,
            event="notifications_updated",
            data={
                "action": "multiple_marked_read",
                "count": updated_count,
                "notification_ids": notification_ids,
                "timestamp": timezone.now().isoformat()
            }
        )
            
        return Response({'status': 'Notifications marked as read', 'count': updated_count})

    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        deleted_count = Notification.objects.filter(user=request.user).delete()[0]
        
        # Trigger Pusher event to clear all notifications on client
        trigger_notification(
            user_id=request.user.id,
            event="notifications_cleared",
            data={
                "action": "all_cleared",
                "count": deleted_count,
                "timestamp": timezone.now().isoformat()
            }
        )
        
        return Response({'status': 'All notifications cleared', 'count': deleted_count})

    @action(detail=False, methods=['get'])
    def unread(self, request):
        notifications = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def recent(self, request):
        yesterday = timezone.now() - timedelta(days=1)
        notifications = self.get_queryset().filter(created_at__gte=yesterday)
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        queryset = Notification.objects.filter(user=request.user)
        stats_data = {
            'total_notifications': queryset.count(),
            'unread_count': queryset.filter(is_read=False, is_archived=False).count(),
            'read_count': queryset.filter(is_read=True, is_archived=False).count(),
            'archived_count': queryset.filter(is_archived=True).count(),
            'by_type': dict(queryset.values('notification_type').annotate(count=Count('id')).values_list('notification_type', 'count')),
            'by_priority': dict(queryset.values('priority').annotate(count=Count('id')).values_list('priority', 'count')),
            'recent_unread': NotificationSerializer(queryset.filter(is_read=False, is_archived=False)[:5], many=True).data
        }
        return Response(stats_data)


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NotificationPreference.objects.filter(user=self.request.user)

    def get_object(self):
        obj, _ = NotificationPreference.objects.get_or_create(user=self.request.user)
        return obj

    @action(detail=False, methods=['get'])
    def my_preferences(self, request):
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data)

    @action(detail=False, methods=['patch'])
    def update_preferences(self, request):
        obj = self.get_object()
        serializer = self.get_serializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class NotificationDeviceViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationDeviceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NotificationDevice.objects.filter(user=self.request.user)

    def get_serializer_context(self):
        return {'user': self.request.user}

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        device = self.get_object()
        device.is_active = False
        device.save()
        return Response({'status': 'Device deactivated'})


class NotificationTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsAuthenticated]
    queryset = NotificationTemplate.objects.filter(is_active=True)


# ------------------------ API Views ------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_notification(request):
    serializer = NotificationCreateSerializer(data=request.data, context={'user': request.user})
    if serializer.is_valid():
        notification = serializer.save()
        return Response(NotificationSerializer(notification).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_bulk_notifications(request):
    if not request.user.is_staff:
        return Response({'error': 'Only staff can send bulk notifications'}, status=status.HTTP_403_FORBIDDEN)
    serializer = BulkNotificationSerializer(data=request.data)
    if serializer.is_valid():
        notifications = serializer.create_notifications()
        
        # Trigger Pusher for each user
        for notification in notifications:
            trigger_notification(
                user_id=notification.user.id,
                event="new_notification",
                data={
                    "id": notification.id,
                    "notification_id": str(notification.notification_id),
                    "title": notification.title,
                    "message": notification.message,
                    "notification_type": notification.notification_type,
                    "priority": notification.priority,
                    "metadata": notification.metadata or {},
                    "created_at": notification.created_at.isoformat(),
                    "is_read": notification.is_read,
                    "action_url": notification.action_url or "",
                    "action_label": notification.action_label or ""
                }
            )
            
        return Response({'status': 'Notifications sent', 'count': len(notifications)}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_template_notification(request):
    template_type = request.data.get('template_type')
    context_data = request.data.get('context', {})

    try:
        template = NotificationTemplate.objects.get(template_type=template_type, is_active=True)
        rendered = template.render(context_data)
        notification = Notification.objects.create(
            user=request.user,
            notification_type=rendered.get('notification_type', 'general'),
            title=rendered.get('title', 'Notification'),
            message=rendered.get('message', ''),
            priority=rendered.get('priority', 'medium'),
            action_url=rendered.get('action_url', ''),
            action_label=rendered.get('action_label', '')
        )
        
        # Trigger Pusher event for template notification
        trigger_notification(
            user_id=request.user.id,
            event="new_notification",
            data={
                "id": notification.id,
                "notification_id": str(notification.notification_id),
                "title": notification.title,
                "message": notification.message,
                "notification_type": notification.notification_type,
                "priority": notification.priority,
                "metadata": notification.metadata or {},
                "created_at": notification.created_at.isoformat(),
                "is_read": notification.is_read,
                "action_url": notification.action_url or "",
                "action_label": notification.action_label or ""
            }
        )
        
        return Response(NotificationSerializer(notification).data, status=status.HTTP_201_CREATED)
    except NotificationTemplate.DoesNotExist:
        return Response({'error': 'Template not found'}, status=status.HTTP_404_NOT_FOUND)
    except KeyError as e:
        return Response({'error': f'Missing context variable: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_count(request):
    count = Notification.objects.filter(user=request.user, is_read=False, is_archived=False).count()
    return Response({'unread_count': count})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_summary(request):
    notifications = Notification.objects.filter(user=request.user, is_archived=False)
    summary = notifications.values('notification_type').annotate(
        total=Count('id'),
        unread=Count('id', filter=Q(is_read=False))
    )
    return Response({'summary': list(summary), 'total_unread': notifications.filter(is_read=False).count()})