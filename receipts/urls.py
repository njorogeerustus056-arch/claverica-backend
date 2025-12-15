from django.urls import path
from . import views

urlpatterns = [
    # Upload
    path("upload/", views.upload_receipt_view, name="upload_receipt"),
    
    # List and filter
    path("list/", views.list_receipts_view, name="list_receipts"),
    
    # Detail, update, delete
    path("<uuid:receipt_id>/", views.get_receipt_detail_view, name="receipt_detail"),
    path("<uuid:receipt_id>/update/", views.update_receipt_view, name="update_receipt"),
    path("<uuid:receipt_id>/delete/", views.delete_receipt_view, name="delete_receipt"),
    
    # Signed URL
    path("signed-url/", views.get_signed_url_view, name="get_signed_url"),
    
    # Statistics
    path("stats/", views.get_receipt_stats_view, name="receipt_stats"),
]
