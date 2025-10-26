from django.urls import path
from . import views

urlpatterns = [
    path("upload/", views.upload_receipt_view, name="upload_receipt"),
    path("list/", views.list_receipts_view, name="list_receipts"),
    path("signed-url/", views.get_signed_url_view, name="get_signed_url"),
]
