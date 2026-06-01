"""
Schema package - re-exports from parent schemas.py and includes translation schemas.

Note: The schemas/ directory shadows the schemas.py file, so we need to
explicitly load schemas.py using importlib to re-export its classes.
"""

import importlib.util
from pathlib import Path

# Import translation schemas from this package
from .translation import (
    TranslationRequest,
    BulkTranslationRequest,
    TranslationResponse,
    BulkTranslationResponse,
    LanguageInfo,
    LanguagesResponse,
    TranslationErrorResponse,
)

# Load the parent schemas.py module directly by file path
_schemas_path = Path(__file__).parent.parent / "schemas.py"
_spec = importlib.util.spec_from_file_location("_schemas_module", _schemas_path)
_schemas_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_schemas_module)

# Re-export all schema classes from schemas.py
TenantCreate = _schemas_module.TenantCreate
TenantResponse = _schemas_module.TenantResponse
TenantUpdate = _schemas_module.TenantUpdate
RoleCreate = _schemas_module.RoleCreate
RoleResponse = _schemas_module.RoleResponse
RoleUpdate = _schemas_module.RoleUpdate
UserCreate = _schemas_module.UserCreate
UserLogin = _schemas_module.UserLogin
UserResponse = _schemas_module.UserResponse
UserDetailResponse = _schemas_module.UserDetailResponse
UserUpdate = _schemas_module.UserUpdate
UserProfileResponse = _schemas_module.UserProfileResponse
UserProfileUpdate = _schemas_module.UserProfileUpdate
DocumentCreate = _schemas_module.DocumentCreate
DocumentResponse = _schemas_module.DocumentResponse
DocumentDeleteResponse = _schemas_module.DocumentDeleteResponse
DocumentStatsResponse = _schemas_module.DocumentStatsResponse
ComplianceReportResponse = _schemas_module.ComplianceReportResponse
TokenResponse = _schemas_module.TokenResponse
AuthSessionResponse = _schemas_module.AuthSessionResponse
LoginAttemptResponse = _schemas_module.LoginAttemptResponse
RefreshRequest = _schemas_module.RefreshRequest
NotificationResponse = _schemas_module.NotificationResponse
KPIData = _schemas_module.KPIData
LastAnalysisItem = _schemas_module.LastAnalysisItem
TeamActivityItem = _schemas_module.TeamActivityItem
StatusDistribution = _schemas_module.StatusDistribution
AuditLogResponse = _schemas_module.AuditLogResponse
ErrorResponse = _schemas_module.ErrorResponse
PaginatedResponse = _schemas_module.PaginatedResponse
DashboardResponse = _schemas_module.DashboardResponse
RegisterRequest = _schemas_module.RegisterRequest
RegisterResponse = _schemas_module.RegisterResponse
AdminDashboardResponse = _schemas_module.AdminDashboardResponse
UserDashboardResponse = _schemas_module.UserDashboardResponse
PasswordResetRequest = _schemas_module.PasswordResetRequest
PasswordResetConfirm = _schemas_module.PasswordResetConfirm
PasswordResetResponse = _schemas_module.PasswordResetResponse
ChangePasswordRequest = _schemas_module.ChangePasswordRequest
ChangePasswordResponse = _schemas_module.ChangePasswordResponse
SessionRevokeResponse = _schemas_module.SessionRevokeResponse
UserInvitationRequest = _schemas_module.UserInvitationRequest
AcceptInvitationRequest = _schemas_module.AcceptInvitationRequest
AcceptInvitationResponse = _schemas_module.AcceptInvitationResponse
AnalyseStatsResponse = _schemas_module.AnalyseStatsResponse
AnalyseRequestSchema = _schemas_module.AnalyseRequestSchema
AnalyseResultResponse = _schemas_module.AnalyseResultResponse
AnalyseHistoryItemResponse = _schemas_module.AnalyseHistoryItemResponse

__all__ = [
    "TenantCreate", "TenantResponse", "TenantUpdate",
    "RoleCreate", "RoleResponse", "RoleUpdate",
    "UserCreate", "UserLogin", "UserResponse", "UserDetailResponse",
    "UserUpdate", "UserProfileResponse", "UserProfileUpdate",
    "DocumentCreate", "DocumentResponse", "DocumentDeleteResponse",
    "DocumentStatsResponse", "ComplianceReportResponse",
    "TokenResponse", "AuthSessionResponse", "LoginAttemptResponse",
    "RefreshRequest",
    "NotificationResponse",
    "KPIData", "LastAnalysisItem", "TeamActivityItem", "StatusDistribution",
    "AuditLogResponse",
    "ErrorResponse", "PaginatedResponse", "DashboardResponse",
    "RegisterRequest", "RegisterResponse",
    "AdminDashboardResponse", "UserDashboardResponse",
    "PasswordResetRequest", "PasswordResetConfirm", "PasswordResetResponse",
    "ChangePasswordRequest", "ChangePasswordResponse", "SessionRevokeResponse",
    "UserInvitationRequest", "AcceptInvitationRequest", "AcceptInvitationResponse",
    "AnalyseStatsResponse", "AnalyseRequestSchema", "AnalyseResultResponse",
    "AnalyseHistoryItemResponse",
    "TranslationRequest",
    "BulkTranslationRequest",
    "TranslationResponse",
    "BulkTranslationResponse",
    "LanguageInfo",
    "LanguagesResponse",
    "TranslationErrorResponse",
]
