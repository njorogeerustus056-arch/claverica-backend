# receipts/filters.py
import django_filters

from .models import Receipt


class ReceiptFilter(django_filters.FilterSet):
    """
    FilterSet for filtering receipts on list endpoint.

    Supported query params:
      ?type=invoice           - exact match on type
      ?customer=John          - case-insensitive partial match on customer_name
      ?year=2025              - filter by year of date
      ?month=03               - filter by month of date
      ?date_after=2025-01-01  - filter receipts on or after date
      ?date_before=2025-12-31 - filter receipts on or before date
    """

    type = django_filters.ChoiceFilter(
        choices=Receipt.TYPE_CHOICES,
        help_text="Filter by receipt type (invoice, refund, credit_note).",
    )
    customer = django_filters.CharFilter(
        field_name="customer_name",
        lookup_expr="icontains",
        help_text="Case-insensitive partial match on customer name.",
    )
    year = django_filters.NumberFilter(
        field_name="date",
        lookup_expr="year",
        help_text="Filter by 4-digit year (e.g. 2025).",
    )
    month = django_filters.NumberFilter(
        field_name="date",
        lookup_expr="month",
        help_text="Filter by month number (1-12).",
    )
    date_after = django_filters.DateFilter(
        field_name="date",
        lookup_expr="gte",
        help_text="Filter receipts issued on or after this date (YYYY-MM-DD).",
    )
    date_before = django_filters.DateFilter(
        field_name="date",
        lookup_expr="lte",
        help_text="Filter receipts issued on or before this date (YYYY-MM-DD).",
    )

    class Meta:
        model = Receipt
        fields = ["type", "customer", "year", "month", "date_after", "date_before"]