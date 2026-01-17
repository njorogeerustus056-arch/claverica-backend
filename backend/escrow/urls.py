# escrow/urls.py - UPDATED TO USE CENTRAL COMPLIANCE SYSTEM

from django.urls import path
from . import views
# REMOVED: from . import compliance_views  # No longer needed

urlpatterns = [
    # Base endpoint
    path('', views.index, name='escrow_index'),
    
    # CRUD operations
    path('create/', views.create_escrow_view, name='create_escrow'),
    path('list/', views.list_escrows_view, name='list_escrows'),
    path('<int:escrow_id>/', views.get_escrow_detail_view, name='escrow_detail'),
    path('<int:escrow_id>/update/', views.update_escrow_view, name='update_escrow'),
    
    # Escrow actions
    path('<int:escrow_id>/fund/', views.fund_escrow_view, name='fund_escrow'),
    path('<int:escrow_id>/release/', views.release_escrow_view, name='release_escrow'),
    path('<int:escrow_id>/dispute/', views.dispute_escrow_view, name='dispute_escrow'),
    
    # Stats
    path('stats/', views.get_escrow_stats_view, name='escrow_stats'),
    
    # ALL COMPLIANCE ROUTES REMOVED - USE CENTRAL COMPLIANCE APP
    # To create a compliance request for escrow dispute:
    # POST /api/compliance/api/integration/create-request/
    # with payload: {app_name: 'escrow', app_transaction_id: escrow_id, request_type: 'dispute_resolution'}
]