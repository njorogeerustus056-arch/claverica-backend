"""
compliance/__init__.py - Package initialization
"""

default_app_config = 'compliance.apps.ComplianceConfig'

__version__ = '1.0.0'
__author__ = 'ClaveRica Team'
__description__ = 'Central Compliance Management System'

# Import key components for easier access
from .models import (
    ComplianceRequest, KYCVerification, KYCDocument,
    TACRequest, VideoCallSession, ComplianceAuditLog,
    ComplianceRule, ComplianceDashboardStats, ComplianceAlert
)

from .services import (
    ComplianceService, KYCService, TACService,
    VideoCallService, DocumentService, AuditService,
    AlertService, ScheduledTasksService
)

# Export commonly used classes
__all__ = [
    # Models
    'ComplianceRequest',
    'KYCVerification',
    'KYCDocument',
    'TACRequest',
    'VideoCallSession',
    'ComplianceAuditLog',
    'ComplianceRule',
    'ComplianceDashboardStats',
    'ComplianceAlert',
    
    # Services
    'ComplianceService',
    'KYCService',
    'TACService',
    'VideoCallService',
    'DocumentService',
    'AuditService',
    'AlertService',
    'ScheduledTasksService',
]