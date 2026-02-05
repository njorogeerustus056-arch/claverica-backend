# notifications/urls.py - FIXED ORDER
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.NotificationViewSet, basename='notification')

urlpatterns = [
    # ✅✅✅ PUT SPECIFIC ENDPOINTS FIRST
    path('unread-count/', views.UnreadCountView.as_view(), name='unread_count'),
    path('mark-read/<int:pk>/', views.MarkAsReadView.as_view(), name='mark_read'),
    path('mark-all-read/', views.MarkAllAsReadView.as_view(), name='mark_all_read'),
    
    # Then the router
    path('', include(router.urls)),
    
    # Admin endpoints
    path('admin/alerts/', views.AdminAlertsView.as_view(), name='admin_alerts'),
    path('admin/action-required/', views.AdminActionRequiredView.as_view(), name='admin_action_required'),
    
    # Preferences
    path('preferences/', views.NotificationPreferencesView.as_view(), name='notification_preferences'),
]