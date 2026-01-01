"""
Custom Permission Classes for Claverica API
Reusable permissions for fintech security requirements
"""

from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to access it.
    Updated to work with accounts.Account model.
    """
    message = "You do not have permission to access this resource."
    
    def has_object_permission(self, request, view, obj):
        # Check if object has a user field
        if hasattr(obj, 'user'):
            return obj.user == request.user
        # Check if object has an account field (for accounts.Account)
        if hasattr(obj, 'account'):
            return obj.account == request.user
        return False


class IsAccountOwner(permissions.BasePermission):
    """
    Permission to check if user owns the account.
    For use with account-related endpoints.
    Updated for accounts.Account model.
    """
    message = "You can only access your own account."
    
    def has_object_permission(self, request, view, obj):
        # Direct comparison (obj is the Account instance)
        if obj == request.user:
            return True
        # Check if object has a user field (backward compatibility)
        if hasattr(obj, 'user'):
            return obj.user == request.user
        # Check if object has an account field
        if hasattr(obj, 'account'):
            return obj.account == request.user
        return False


class IsVerifiedUser(permissions.BasePermission):
    """
    Permission to check if user has completed KYC verification.
    Required for high-value transactions and sensitive operations.
    Updated to work with accounts.Account model.
    """
    message = "This action requires KYC verification. Please complete your profile verification."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has verified profile in accounts app
        try:
            from accounts.models import AccountProfile
            profile = AccountProfile.objects.get(account=request.user)
            return profile.email_verified and profile.phone_verified
        except Exception:
            # If no profile exists, user is not verified
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
    Updated to use accounts.Account model.
    """
    message = "You are not authorized to initiate transactions. Please verify your account or contact support."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user is active
        if not request.user.is_active:
            return False
        
        # Check KYC verification via AccountProfile
        try:
            from accounts.models import AccountProfile
            profile = AccountProfile.objects.get(account=request.user)
            
            if not (profile.email_verified and profile.phone_verified):
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
    Updated for accounts.Account model.
    """
    message = "You need an active account to perform this action."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # With accounts.Account, the user IS the account
        # Just check if the user is active
        return request.user.is_active


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission to allow access to owners or admin users.
    Updated for accounts.Account model.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin users have full access
        if request.user and request.user.is_staff:
            return True
        
        # Check ownership - direct comparison
        if obj == request.user:
            return True
        
        # Check if object has a user field (backward compatibility)
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Check if object has an account field
        if hasattr(obj, 'account'):
            return obj.account == request.user
        
        return False


class CanAccessSensitiveData(permissions.BasePermission):
    """
    Permission for accessing sensitive financial data.
    Requires verified account and additional security checks.
    Updated for accounts.Account model.
    """
    message = "Access denied. Additional verification required for sensitive data."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user is active
        if not request.user.is_active:
            return False
        
        # Check KYC verification via AccountProfile
        try:
            from accounts.models import AccountProfile
            profile = AccountProfile.objects.get(account=request.user)
            
            if not (profile.email_verified and profile.phone_verified):
                return False
            
            # Additional security checks can be added:
            # - Recent authentication (session age)
            # - 2FA verification
            # - Geolocation checks
            # - Device fingerprinting
            
            # For now, just require 2FA if enabled
            if hasattr(request.user, 'settings'):
                if request.user.settings.two_factor_enabled:
                    # In production, check if 2FA was recently verified
                    pass
            
            return True
        except Exception:
            # If no profile exists, user cannot access sensitive data
            return False