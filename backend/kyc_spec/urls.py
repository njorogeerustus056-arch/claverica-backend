# kyc_spec/urls.py
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from . import views

urlpatterns = [
    # Core collection endpoints
    path('collect/', views.KycSpecCollectView.as_view(), name='kyc-spec-collect'),
    path('collect-legacy/', views.kyc_spec_collect_legacy, name='kyc-spec-collect-legacy'),
    path('stats/', views.KycSpecStatsView.as_view(), name='kyc-spec-stats'),
    
    # Dashboard & Management
    path('dashboard/', views.KycSpecDashboardView.as_view(), name='kyc-spec-dashboard'),
    path('summary/', views.kyc_spec_summary, name='kyc-spec-summary'),
    path('recent/', views.kyc_spec_recent, name='kyc-spec-recent'),
    
    # Search & Export
    path('search/', views.KycSpecSearchView.as_view(), name='kyc-spec-search'),
    path('export/', views.KycSpecExportView.as_view(), name='kyc-spec-export'),
    
    # Individual submission management
    path('submission/<uuid:submission_id>/update-status/', 
         views.KycSpecUpdateStatusView.as_view(), 
         name='kyc-spec-update-status'),
]
