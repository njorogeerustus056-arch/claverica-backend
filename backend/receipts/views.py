# receipts/views.py
import mimetypes
import os

from django.http import FileResponse, Http404
from django.utils.text import slugify
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import ReceiptFilter
from .models import Receipt
from .pagination import ReceiptPagination
from .permissions import IsAdminOrReadOnly
from .serializers import ReceiptSerializer, ReceiptUploadSerializer


class ReceiptListView(generics.ListAPIView):
    """
    GET /api/receipts/

    Returns a paginated, filterable list of receipts ordered
    by date descending. Accessible by any authenticated user.

    Query params:
      ?type=invoice|refund|credit_note
      ?customer=<partial name>
      ?year=<YYYY>
      ?month=<1-12>
      ?date_after=<YYYY-MM-DD>
      ?date_before=<YYYY-MM-DD>
      ?page_size=<N>  (max 100)
    """

    queryset = Receipt.objects.select_related("uploaded_by").all()
    serializer_class = ReceiptSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    pagination_class = ReceiptPagination
    filterset_class = ReceiptFilter
    ordering = ["-date", "-uploaded_at"]


class ReceiptCreateView(generics.CreateAPIView):
    """
    POST /api/receipts/upload/

    Allows admin users to upload a new PDF receipt with metadata.
    Accepts multipart/form-data.

    Fields: type, amount, date, customer_name, pdf_file
    """

    queryset = Receipt.objects.all()
    serializer_class = ReceiptUploadSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        """Restrict upload to admin users and auto-set uploaded_by."""
        if not self.request.user.is_staff:
            raise PermissionDenied("Only admin users can upload receipts.")
        serializer.save(uploaded_by=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Return full read representation after creation
        read_serializer = ReceiptSerializer(
            serializer.instance,
            context={"request": request},
        )
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)


class ReceiptDetailView(generics.RetrieveAPIView):
    """
    GET /api/receipts/{id}/

    Returns metadata for a single receipt.
    Accessible by any authenticated user.
    """

    queryset = Receipt.objects.select_related("uploaded_by").all()
    serializer_class = ReceiptSerializer
    permission_classes = [IsAuthenticated]


class ReceiptDownloadView(APIView):
    """
    GET /api/receipts/{id}/download/

    Streams the PDF file to the client as an attachment download.
    Accessible by any authenticated user.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        """Return the PDF file as a streaming download response."""
        try:
            receipt = Receipt.objects.get(pk=pk)
        except Receipt.DoesNotExist:
            raise Http404("Receipt not found.")

        file_path = receipt.pdf_file.path
        if not os.path.isfile(file_path):
            return Response(
                {"detail": "PDF file not found on server."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Build a safe filename for the Content-Disposition header
        safe_name = slugify(f"{receipt.get_type_display()}-{receipt.customer_name}-{receipt.date}")
        filename = f"{safe_name}.pdf"

        response = FileResponse(
            open(file_path, "rb"),
            content_type="application/pdf",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class ReceiptDeleteView(generics.DestroyAPIView):
    """
    DELETE /api/receipts/{id}/

    Deletes a receipt record and its associated PDF file from disk.
    Admin-only access.
    """

    queryset = Receipt.objects.all()
    permission_classes = [IsAuthenticated]

    def perform_destroy(self, instance):
        """Restrict deletion to admin users."""
        if not self.request.user.is_staff:
            raise PermissionDenied("Only admin users can delete receipts.")
        # Model.delete() handles file removal from disk
        instance.delete()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"detail": "Receipt deleted successfully."},
            status=status.HTTP_200_OK,
        )