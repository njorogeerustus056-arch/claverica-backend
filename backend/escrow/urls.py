# escrow/urls.py - UPDATED WITH COMPLIANCE INTEGRATION

from django.urls import path
from . import views
from . import compliance_views  # NEW: Import compliance views

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
    
    # NEW: Compliance Integration Routes
    path('<int:escrow_id>/compliance/dispute/', compliance_views.request_dispute_resolution, name='compliance-dispute'),
    path('<int:escrow_id>/compliance/kyc/', compliance_views.request_kyc_verification, name='compliance-kyc'),
    path('<int:escrow_id>/compliance/verify-tac/', compliance_views.verify_tac_for_release, name='compliance-verify-tac'),
    path('<int:escrow_id>/compliance/submit-form/', compliance_views.submit_compliance_form, name='compliance-submit-form'),
    path('<int:escrow_id>/compliance/manual-release/', compliance_views.request_manual_release_approval, name='compliance-manual-release'),
    path('<int:escrow_id>/compliance/status/', compliance_views.get_escrow_compliance_status, name='compliance-status'),
    
    # NEW: Admin Compliance Routes
    path('admin/compliance/dashboard/', compliance_views.admin_escrow_compliance_dashboard, name='admin-compliance-dashboard'),
    
    # Stats
    path('stats/', views.get_escrow_stats_view, name='escrow_stats'),
]