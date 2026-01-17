"""
compliance/permissions.py - Custom permissions for compliance app
"""

from rest_framework import permissions
from django.contrib.auth import get_user_model

from .models import KYCVerification, VerificationStatus



class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission to only allow owners of an object or admins to access it.
    The object must have a 'user_id' field.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin users have full access
        if request.user.is_staff:
            return True
        
        # Check if object has user_id attribute
        if hasattr(obj, 'user_id'):
            return str(obj.user_id) == str(request.user.id)
        
        # Check if object has user attribute
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class HasKYCApproved(permissions.BasePermission):
    """
    Permission to only allow users with approved KYC to access.
    """
    
    def has_permission(self, request, view):
        # Admin users bypass KYC check
        if request.user.is_staff:
            return True
        
        # Check if user has approved KYC
        verification = KYCVerification.objects.filter(
            user_id=str(request.user.id),
            verification_status=VerificationStatus.APPROVED
        ).first()
        
        return verification is not None


class IsComplianceOfficer(permissions.BasePermission):
    """
    Permission for compliance officers only.
    Checks if user is in 'Compliance Officers' group.
    """
    
    def has_permission(self, request, view):
        # Superusers are always compliance officers
        if request.user.is_superuser:
            return True
        
        # Check if user is in compliance officers group
        return request.user.groups.filter(name='Compliance Officers').exists()


class HasKYCInProgress(permissions.BasePermission):
    """
    Permission to allow access if user has KYC in progress.
    Used for document upload after KYC submission.
    """
    
    def has_permission(self, request, view):
        # Admin users bypass this check
        if request.user.is_staff:
            return True
        
        # Check if user has any KYC verification (not rejected or expired)
        verification = KYCVerification.objects.filter(
            user_id=str(request.user.id)
        ).exclude(
            verification_status__in=[VerificationStatus.REJECTED, VerificationStatus.EXPIRED]
        ).first()
        
        return verification is not None


class CanProcessWithdrawal(permissions.BasePermission):
    """
    Permission to process withdrawals (for compliance officers and processors).
    """
    
    def has_permission(self, request, view):
        # Only allow POST, PUT, PATCH methods
        if request.method not in ['POST', 'PUT', 'PATCH']:
            return True
        
        # Check if user is staff or in processors group
        if request.user.is_staff:
            return True
        
        return request.user.groups.filter(name__in=['Compliance Officers', 'Payment Processors']).exists()


class CanViewAuditLogs(permissions.BasePermission):
    """
    Permission to view audit logs.
    Users can only see their own logs, admins can see all.
    """
    
    def has_permission(self, request, view):
        # Only allow safe methods (GET, HEAD, OPTIONS)
        if request.method not in permissions.SAFE_METHODS:
            return request.user.is_staff
        
        return True
    
    def has_object_permission(self, request, view, obj):
        # Admin users can see all logs
        if request.user.is_staff:
            return True
        
        # Users can only see their own logs
        return str(obj.user_id) == str(request.user.id)


class CanManageDocuments(permissions.BasePermission):
    """
    Permission to manage KYC documents.
    Users can upload their own documents, admins can manage all.
    """
    
    def has_permission(self, request, view):
        # Admin users have full access
        if request.user.is_staff:
            return True
        
        # Users can create documents (upload)
        if view.action == 'create':
            return True
        
        # For other actions, check object permission
        return True
    
    def has_object_permission(self, request, view, obj):
        # Admin users have full access
        if request.user.is_staff:
            return True
        
        # Users can only manage their own documents
        return str(obj.user_id) == str(request.user.id)


class CanApproveKYC(permissions.BasePermission):
    """
    Permission to approve/reject KYC verifications.
    Only for compliance officers and admins.
    """
    
    def has_permission(self, request, view):
        # Only allow specific actions
        if view.action not in ['approve', 'reject']:
            return True
        
        return request.user.is_staff or request.user.groups.filter(name='Compliance Officers').exists()
    
    def has_object_permission(self, request, view, obj):
        # For approve/reject actions, check permission
        if view.action in ['approve', 'reject']:
            return request.user.is_staff or request.user.groups.filter(name='Compliance Officers').exists()
        
        return True


class HasWithdrawalPermissions(permissions.BasePermission):
    """
    Combined permissions for withdrawal operations.
    """
    
    def has_permission(self, request, view):
        # Different permissions based on action
        if view.action == 'create':
            # Need approved KYC to create withdrawal
            from .models import KYCVerification, VerificationStatus
            verification = KYCVerification.objects.filter(
                user_id=str(request.user.id),
                verification_status=VerificationStatus.APPROVED
            ).first()
            
            if not verification:
                return False
            
            return True
        
        elif view.action in ['verify_tac', 'cancel']:
            # Users can verify/cancel their own withdrawals
            return True
        
        elif view.action in ['update', 'partial_update']:
            # Only staff can update withdrawals
            return request.user.is_staff
        
        return True
    
    def has_object_permission(self, request, view, obj):
        # Users can access their own withdrawals
        if str(obj.user_id) == str(request.user.id):
            return True
        
        # Staff can access all withdrawals
        if request.user.is_staff:
            return True
        
        return False


class CompliancePermissionMixin:
    """
    Mixin to add compliance-specific permission checks to views.
    """
    
    def get_permissions(self):
        """
        Instantiate and return the list of permissions that this view requires.
        """
        permissions = super().get_permissions()
        
        # Add additional permission checks based on action
        if self.action == 'approve' or self.action == 'reject':
            permissions.append(CanApproveKYC())
        elif self.action == 'download':
            permissions.append(CanManageDocuments())
        
        return permissions