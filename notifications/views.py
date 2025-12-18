# notifications/views.py
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


class NotificationViewSet(viewsets.ModelViewSet):
    """Manage user notifications"""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return NotificationCreateSerializer
        return NotificationSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Notification.objects.filter(user=user)

        # Optional filters
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
        context = super().get_serializer_context()
        context['user'] = self.request.user
        return context

    # ------------------------ Single notification actions ------------------------
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.mark_as_read()
        return Response({'status': 'Notification marked as read'})

    @action(detail=True, methods=['post'])
    def mark_as_unread(self, request, pk=None):
        notification = self.get_object()
        notification.mark_as_unread()
        return Response({'status': 'Notification marked as unread'})

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        notification = self.get_object()
        notification.archive()
        return Response({'status': 'Notification archived'})

    # ------------------------ Bulk actions ------------------------
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        updated_count = Notification.objects.filter(
            user=request.user,
            is_read=False,
            is_archived=False
        ).update(is_read=True, read_at=timezone.now())

        return Response({'status': 'All notifications marked as read', 'count': updated_count})

    @action(detail=False, methods=['post'])
    def mark_multiple_as_read(self, request):
        serializer = MarkAsReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notification_ids = serializer.validated_data['notification_ids']

        updated_count = Notification.objects.filter(
            id__in=notification_ids,
            user=request.user
        ).update(is_read=True, read_at=timezone.now())

        return Response({'status': 'Notifications marked as read', 'count': updated_count})

    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        deleted_count = Notification.objects.filter(user=request.user).delete()[0]
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
        total_notifications = queryset.count()
        unread_count = queryset.filter(is_read=False, is_archived=False).count()
        read_count = queryset.filter(is_read=True, is_archived=False).count()
        archived_count = queryset.filter(is_archived=True).count()

        by_type = dict(queryset.values('notification_type').annotate(count=Count('id')).values_list('notification_type', 'count'))
        by_priority = dict(queryset.values('priority').annotate(count=Count('id')).values_list('priority', 'count'))

        recent_unread = queryset.filter(is_read=False, is_archived=False)[:5]

        stats_data = {
            'total_notifications': total_notifications,
            'unread_count': unread_count,
            'read_count': read_count,
            'archived_count': archived_count,
            'by_type': by_type,
            'by_priority': by_priority,
            'recent_unread': NotificationSerializer(recent_unread, many=True).data
        }

        return Response(stats_data)


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    """Manage user notification preferences"""
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NotificationPreference.objects.filter(user=self.request.user)

    def get_object(self):
        obj, created = NotificationPreference.objects.get_or_create(user=self.request.user)
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
    """Manage user notification devices"""
    serializer_class = NotificationDeviceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NotificationDevice.objects.filter(user=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user'] = self.request.user
        return context

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        device = self.get_object()
        device.is_active = False
        device.save()
        return Response({'status': 'Device deactivated'})


class NotificationTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """View active notification templates"""
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsAuthenticated]
    queryset = NotificationTemplate.objects.filter(is_active=True)


# ------------------------ Function-based API endpoints ------------------------
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
        return Response({'error': 'Only staff members can send bulk notifications'}, status=status.HTTP_403_FORBIDDEN)

    serializer = BulkNotificationSerializer(data=request.data)
    if serializer.is_valid():
        notifications = serializer.create_notifications()
        return Response({'status': 'Notifications sent', 'count': len(notifications)}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_template_notification(request):
    template_type = request.data.get('template_type')
    context_data = request.data.get('context', {})

    try:
        template = NotificationTemplate.objects.get(template_type=template_type, is_active=True)
    except NotificationTemplate.DoesNotExist:
        return Response({'error': 'Template not found'}, status=status.HTTP_404_NOT_FOUND)

    try:
        rendered = template.render(context_data)
        notification = Notification.objects.create(
            user=request.user,
            notification_type=rendered['notification_type'],
            title=rendered['title'],
            message=rendered['message'],
            priority=rendered['priority'],
            action_url=rendered.get('action_url', ''),
            action_label=rendered.get('action_label', ''),
        )
        return Response(NotificationSerializer(notification).data, status=status.HTTP_201_CREATED)
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
