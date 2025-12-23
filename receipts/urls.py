from django.urls import path
from . import views

urlpatterns = [
    # Upload a receipt
    path("upload/", views.upload_receipt_view, name="upload_receipt"),
    
    # List receipts with pagination/filter
    path("list/", views.list_receipts_view, name="list_receipts"),
    
    # Receipt detail
    path("<uuid:receipt_id>/", views.get_receipt_detail_view, name="receipt_detail"),
    
    # Update receipt
    path("<uuid:receipt_id>/update/", views.update_receipt_view, name="update_receipt"),
    
    # Delete receipt
    path("<uuid:receipt_id>/delete/", views.delete_receipt_view, name="delete_receipt"),
    
    # Receipt stats
    path("stats/", views.get_receipt_stats_view, name="receipt_stats"),
]
