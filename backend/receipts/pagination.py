# receipts/pagination.py
from rest_framework.pagination import PageNumberPagination


class ReceiptPagination(PageNumberPagination):
    """
    Pagination configuration for receipt list endpoints.

    Defaults to 20 items per page, max 100.
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100