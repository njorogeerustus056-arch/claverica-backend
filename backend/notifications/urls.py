# notifications/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register viewsets
router = DefaultRouter()
router.register(r'notifications', views.NotificationViewSet, basename='notification')
router.register(r'preferences', views.NotificationPreferenceViewSet, basename='notification-preference')
router.register(r'devices', views.NotificationDeviceViewSet, basename='notification-device')
router.register(r'templates', views.NotificationTemplateViewSet, basename='notification-template')

# URL patterns
urlpatterns = [
    # Include all router-registered viewsets
    path('', include(router.urls)),

    # Function-based API endpoints
    path('send/', views.send_notification, name='send-notification'),
    path('send-bulk/', views.send_bulk_notifications, name='send-bulk-notifications'),
    path('send-template/', views.send_template_notification, name='send-template-notification'),
    path('count/', views.notification_count, name='notification-count'),
    path('summary/', views.notification_summary, name='notification-summary'),
]