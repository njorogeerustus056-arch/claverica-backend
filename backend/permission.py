"""
Custom Permission Classes for Claverica API
Reusable permissions for fintech security requirements
"""

from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to access it.
    Assumes the model has a 'user' field.
    """
    message = "You do not have permission to access this resource."
    
    def has_object_permission(self, request, view, obj):
        # Check if object has a user field
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False


class IsAccountOwner(permissions.BasePermission):
    """
    Permission to check if user owns the account.
    For use with account-related endpoints.
    """
    message = "You can only access your own account."
    
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'account') and hasattr(obj.account, 'user'):
            return obj.account.user == request.user
        return False


class IsVerifiedUser(permissions.BasePermission):
    """
    Permission to check if user has completed KYC verification.
    Required for high-value transactions and sensitive operations.
    """
    message = "This action requires KYC verification. Please complete your profile verification."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has verified account
        # Adjust this based on your Account model structure
        try:
            from payments.models import Account
            account = Account.objects.filter(
                user=request.user,
                is_verified=True
            ).exists()
            return account
        except Exception:
            return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission to allow read-only access to all users,
    but write access only to admin users.
    """
    
    def has_permission(self, request, view):
        # Read permissions for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for admin users
        return request.user and request.user.is_staff


class IsSuperUserOrReadOnly(permissions.BasePermission):
    """
    Permission for superuser-only write operations.
    Read access for authenticated users.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        return request.user and request.user.is_superuser


class CanInitiateTransaction(permissions.BasePermission):
    """
    Permission to check if user can initiate financial transactions.
    Checks for active account, verification status, and no restrictions.
    """
    message = "You are not authorized to initiate transactions. Please verify your account or contact support."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has active, verified account
        try:
            from payments.models import Account
            account = Account.objects.filter(
                user=request.user,
                is_active=True,
                is_verified=True
            ).exists()
            
            if not account:
                return False
            
            # Additional checks can be added here:
            # - Account not suspended
            # - No pending compliance issues
            # - Within transaction limits
            
            return True
        except Exception:
            return False


class HasActiveAccount(permissions.BasePermission):
    """
    Permission to check if user has at least one active account.
    """
    message = "You need an active account to perform this action."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        try:
            from payments.models import Account
            return Account.objects.filter(
                user=request.user,
                is_active=True
            ).exists()
        except Exception:
            return False


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission to allow access to owners or admin users.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin users have full access
        if request.user and request.user.is_staff:
            return True
        
        # Check ownership
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class CanAccessSensitiveData(permissions.BasePermission):
    """
    Permission for accessing sensitive financial data.
    Requires verified account and additional security checks.
    """
    message = "Access denied. Additional verification required for sensitive data."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user is verified
        try:
            from payments.models import Account
            account = Account.objects.filter(
                user=request.user,
                is_verified=True,
                is_active=True
            ).first()
            
            if not account:
                return False
            
            # Additional security checks can be added:
            # - Recent authentication (session age)
            # - 2FA verification
            # - Geolocation checks
            # - Device fingerprinting
            
            return True
        except Exception:
            return False
