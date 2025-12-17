from django.urls import path
from . import views

app_name = 'compliance'

urlpatterns = [
    # KYC Routes
    path('kyc/submit/', views.submit_kyc, name='kyc_submit'),
    path('kyc/upload-document/', views.upload_kyc_document, name='upload_document'),
    path('kyc/status/<str:user_id>/', views.get_kyc_status, name='kyc_status'),
    
    # TAC Routes
    path('tac/generate/', views.generate_tac, name='generate_tac'),
    path('tac/verify/', views.verify_tac, name='verify_tac'),
    
    # Withdrawal Routes
    path('withdrawal/request/', views.request_withdrawal, name='request_withdrawal'),
    
    # Documents & Audit
    path('verification/documents/<uuid:verification_id>/', views.get_verification_documents, name='verification_documents'),
    path('audit-log/<str:user_id>/', views.get_audit_log, name='audit_log'),
]
