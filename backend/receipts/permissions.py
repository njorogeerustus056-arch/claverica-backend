# receipts/permissions.py
from rest_framework.permissions import BasePermission, IsAuthenticated

SAFE_METHODS = ("GET", "HEAD", "OPTIONS")


class IsAdminOrReadOnly(BasePermission):
    """
    Custom permission:
    - Admin users (is_staff=True): full access (GET, POST, DELETE, etc.)
    - Regular authenticated users: read-only access (GET, HEAD, OPTIONS)
    - Unauthenticated users: denied entirely
    """

    def has_permission(self, request, view):
        # Must be authenticated regardless of method
        if not request.user or not request.user.is_authenticated:
            return False

        # Read-only methods are allowed for all authenticated users
        if request.method in SAFE_METHODS:
            return True

        # Write methods require admin (is_staff)
        return request.user.is_staff