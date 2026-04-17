"""用户模块统一使用的 Pydantic Schema 定义。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal, Optional

from pydantic import BaseModel, EmailStr, Field


@dataclass
class ExternalIdentityPayload:
    issuer: str
    sub: str
    name: Optional[str]
    email: Optional[str]
    raw_claims: dict


class LoginRequest(BaseModel):
    username: str
    password: str
    app_client: str


class RefreshRequest(BaseModel):
    refreshToken: str


class SmsSendRequest(BaseModel):
    mobile: str
    scene: Literal["LOGIN", "REGISTER", "RESET_PASSWORD"]
    app_client: str


class SmsLoginRequest(BaseModel):
    mobile: str
    code: str
    bizNo: str
    app_client: str


class RegisterRequest(BaseModel):
    mobile: str
    code: str
    bizNo: str
    password: str
    inviteCode: Optional[str] = None
    app_client: str


class PasswordVerifyCodeRequest(BaseModel):
    mobile: str
    code: str
    bizNo: str
    app_client: str


class PasswordResetRequest(BaseModel):
    mobile: str
    newPassword: str
    resetToken: str
    app_client: str


class PasswordChangeRequest(BaseModel):
    oldPassword: str
    newPassword: str


class LogoutRequest(BaseModel):
    refreshToken: str


class MockLoginRequest(BaseModel):
    issuer: str
    sub: str
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    email_verified: bool = False
    app_client: str


class OidcLoginRequest(BaseModel):
    id_token: str
    nonce: str
    max_auth_age: Optional[int] = None
    app_client: str


class StatusUpdateRequest(BaseModel):
    status: Literal["ACTIVE", "DISABLED"]


class OrgCreate(BaseModel):
    name: str
    parent_id: Optional[int] = None
    org_type: Literal["AREA", "SCHOOL", "CANTEEN"]


class OrgResponse(BaseModel):
    id: int
    name: str
    parent_id: Optional[int]
    children: List["OrgResponse"] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class TenantCreate(BaseModel):
    name: str
    status: Literal["ACTIVE", "DISABLED"] = "ACTIVE"


class GenericResponse(BaseModel):
    success: bool
    message: str
    request_id: Optional[str] = None
    data: Optional[dict] = None


# ── Admin CRUD Schemas ─────────────────────────────────────────────────────

class UserAdminCreate(BaseModel):
    username: str
    real_name: Optional[str] = None
    mobile: Optional[str] = None
    password: str
    role_type: Literal["REGULATOR", "EXECUTOR"] = "REGULATOR"
    org_id: Optional[int] = None
    role_ids: Optional[List[int]] = None
    gender: Optional[str] = None
    birthday: Optional[str] = None
    canteen_scope: Optional[str] = None
    face_image_url: Optional[str] = None
    health_image_url: Optional[str] = None


class UserAdminUpdate(BaseModel):
    real_name: Optional[str] = None
    mobile: Optional[str] = None
    org_id: Optional[int] = None
    role_ids: Optional[List[int]] = None
    gender: Optional[str] = None
    birthday: Optional[str] = None
    canteen_scope: Optional[str] = None
    status: Optional[Literal["ACTIVE", "DISABLED"]] = None
    face_image_url: Optional[str] = None
    health_image_url: Optional[str] = None


class UserAdminResponse(BaseModel):
    id: int
    username: str
    real_name: Optional[str]
    mobile: Optional[str]
    role_type: str
    status: str
    org_id: Optional[int]
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


class RoleCreate(BaseModel):
    name: str
    role_type: Literal["REGULATOR", "EXECUTOR"] = "REGULATOR"
    level: Optional[str] = None
    permissions_desc: Optional[str] = None


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    role_type: Optional[Literal["REGULATOR", "EXECUTOR"]] = None
    level: Optional[str] = None
    permissions_desc: Optional[str] = None


class RoleResponse(BaseModel):
    id: int
    name: str
    role_type: str
    level: Optional[str] = None
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


class OrgAdminCreate(BaseModel):
    name: str
    parent_id: Optional[int] = None
    org_type: Literal["AREA", "SCHOOL", "CANTEEN"] = "AREA"


class OrgAdminUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None
    org_type: Optional[Literal["AREA", "SCHOOL", "CANTEEN"]] = None


class OrgAdminResponse(BaseModel):
    id: int
    name: str
    parent_id: Optional[int]
    org_type: str
    tenant_id: int
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


class MenuCreate(BaseModel):
    parent_id: Optional[int] = None
    name: str
    path: str = ""
    component: str = ""
    sort: int = 0
    hidden: bool = False


class MenuUpdate(BaseModel):
    parent_id: Optional[int] = None
    name: Optional[str] = None
    path: Optional[str] = None
    component: Optional[str] = None
    sort: Optional[int] = None
    hidden: Optional[bool] = None


class PermissionResponse(BaseModel):
    id: int
    code: str
    name: str

    model_config = {"from_attributes": True}


class RolePermissionAssign(BaseModel):
    permission_codes: List[str] = Field(..., description="要分配的权限代码列表")


class UserRoleAssign(BaseModel):
    role_ids: List[int] = Field(..., description="要分配的角色ID列表")


class AdminPasswordResetRequest(BaseModel):
    new_password: str = Field(..., min_length=6, max_length=64, description="新密码（6-64位）")

