# payments/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'accounts', views.AccountViewSet, basename='account')
router.register(r'transactions', views.TransactionViewSet, basename='transaction')
router.register(r'cards', views.CardViewSet, basename='card')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),
    # Add this alias for the test that expects /dashboard-stats/
    path('dashboard-stats/', views.dashboard_stats, name='dashboard-stats-alias'),
    # Comment out or remove this line:
    # path('quick-transfer/', views.quick_transfer_view, name='quick-transfer-legacy'),
]