import re
import time
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from jwt import InvalidTokenError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.context import UserContext, system_mode_scope
from app.core.deps import get_current_user
from app.core.security import decode_refresh_token, hash_password, normalize_password, verify_password
from app.db.session import get_db
from app.modules.user.models import RefreshToken as RefreshTokenModel, User as UserModel
from app.modules.user.schemas import (
    ExternalIdentityPayload,
    LoginRequest,
    LogoutRequest,
    MenuCreate,
    MenuUpdate,
    MockLoginRequest,
    OidcLoginRequest,
    OrgAdminCreate,
    OrgAdminResponse,
    OrgAdminUpdate,
    OrgResponse,
    PasswordChangeRequest,
    PasswordResetRequest,
    PasswordVerifyCodeRequest,
    PermissionResponse,
    RefreshRequest,
    RegisterRequest,
    RoleCreate,
    RolePermissionAssign,
    RoleResponse,
    RoleUpdate,
    SmsLoginRequest,
    SmsSendRequest,
    StatusUpdateRequest,
    UserAdminCreate,
    UserAdminResponse,
    UserAdminUpdate,
    UserRoleAssign,
    AdminPasswordResetRequest,
)
from app.modules.user.service import (
    assign_permissions_to_role,
    assign_roles_to_user,
    create_new_token_pair,
    create_user_from_external,
    ensure_default_tenant_and_org,
    get_all_permissions,
    get_org_tree_recursive,
    get_permissions_for_role,
    get_permissions_for_user,
    get_roles_for_user,
    get_user_by_email,
    get_user_by_external,
    get_user_by_id,
    get_user_by_username,
    hash_jti,
    initialize_permissions,
    link_external_identity,
    remove_permissions_from_role,
    remove_roles_from_user,
    rotate_refresh_token,
    validate_rbac_consistency,
    verify_id_token,
)
from app.modules.user.models import Menu as MenuModel, Org as OrgModel, Role as RoleModel

router = APIRouter()
settings = get_settings()
ALLOWED_APP_CLIENTS = settings.allowed_app_clients_set
ALLOWED_STATUSES = {"ACTIVE", "DISABLED"}
ALLOWED_SMS_SCENES = {"LOGIN", "REGISTER", "RESET_PASSWORD"}
MOBILE_RE = re.compile(r"^1\d{10}$")
INVITE_CODE_RE = re.compile(r"^[A-Za-z0-9_-]{3,64}$")
SMS_CODE_EXPIRE_SECONDS = 300
SMS_RETRY_AFTER_SECONDS = 60
SMS_MAX_VERIFY_ATTEMPTS = 5
RESET_TOKEN_EXPIRE_SECONDS = 600
PASSWORD_MIN_LENGTH = 6
# 内存态验证码存储，仅用于开发联调环境（无真实短信网关）
SMS_CODE_STORE: dict[str, dict[str, Any]] = {}
SMS_RATE_LIMIT_STORE: dict[str, float] = {}
RESET_TOKEN_STORE: dict[str, dict[str, Any]] = {}


class ExternalIdpAdapter:
    def exchange(self, request: MockLoginRequest) -> ExternalIdentityPayload:
        raise NotImplementedError


class MockIdpAdapter(ExternalIdpAdapter):
    def exchange(self, request: MockLoginRequest) -> ExternalIdentityPayload:
        return ExternalIdentityPayload(
            issuer=request.issuer,
            sub=request.sub,
            name=request.name,
            email=request.email,
            raw_claims=request.model_dump(),
        )


def ok(data=None, msg: str = "success", code: int = 200):
    return {"code": code, "msg": msg, "data": data}


def validate_app_client(app_client: str) -> bool:
    return app_client in ALLOWED_APP_CLIENTS


def is_app_client_allowed(role_type: str, app_client: str) -> bool:
    if role_type == "REGULATOR":
        return app_client.startswith("reg_")
    if role_type == "EXECUTOR":
        return app_client.startswith("exec_")
    return False


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _is_mobile_valid(mobile: str) -> bool:
    return bool(MOBILE_RE.match(mobile))


def _is_invite_code_valid(invite_code: Optional[str]) -> bool:
    if invite_code is None or invite_code == "":
        return True
    return bool(INVITE_CODE_RE.match(invite_code))


def _is_password_valid(password_plain: str) -> bool:
    return PASSWORD_MIN_LENGTH <= len(password_plain) <= 64


def _cleanup_stores() -> None:
    now_ts = time.time()
    for biz_no, payload in list(SMS_CODE_STORE.items()):
        if float(payload.get("expire_at", 0)) < now_ts:
            SMS_CODE_STORE.pop(biz_no, None)
    for key, next_allowed in list(SMS_RATE_LIMIT_STORE.items()):
        if next_allowed < now_ts:
            SMS_RATE_LIMIT_STORE.pop(key, None)
    for reset_token, payload in list(RESET_TOKEN_STORE.items()):
        if float(payload.get("expire_at", 0)) < now_ts or bool(payload.get("used")):
            RESET_TOKEN_STORE.pop(reset_token, None)


def _verify_sms_code(mobile: str, code: str, biz_no: str, scene: str) -> Optional[JSONResponse]:
    _cleanup_stores()
    payload = SMS_CODE_STORE.get(biz_no)
    if not payload:
        return JSONResponse(status_code=400, content=ok(msg="verification code invalid", code=46001))

    if payload.get("mobile") != mobile or payload.get("scene") != scene:
        return JSONResponse(status_code=400, content=ok(msg="verification code invalid", code=46001))

    now_ts = time.time()
    if float(payload.get("expire_at", 0)) < now_ts:
        SMS_CODE_STORE.pop(biz_no, None)
        return JSONResponse(status_code=400, content=ok(msg="verification code expired", code=46002))

    verify_attempts = int(payload.get("verify_attempts", 0))
    if verify_attempts >= SMS_MAX_VERIFY_ATTEMPTS:
        return JSONResponse(status_code=400, content=ok(msg="verification attempts exceeded", code=46003))

    if payload.get("code") != code:
        verify_attempts += 1
        payload["verify_attempts"] = verify_attempts
        if verify_attempts >= SMS_MAX_VERIFY_ATTEMPTS:
            return JSONResponse(status_code=400, content=ok(msg="verification attempts exceeded", code=46003))
        return JSONResponse(status_code=400, content=ok(msg="verification code invalid", code=46001))

    SMS_CODE_STORE.pop(biz_no, None)
    return None


def _ensure_regulator(current_user: UserModel) -> Optional[JSONResponse]:
    if current_user.role_type != "REGULATOR":
        return JSONResponse(status_code=403, content=ok(msg="forbidden", code=403))
    return None


@router.post("/api/v1/auth/login")
@router.post("/auth/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    if not validate_app_client(req.app_client):
        return JSONResponse(status_code=400, content=ok(msg="invalid app_client", code=400))

    with system_mode_scope():
        user = await get_user_by_username(db, req.username)

    password_plain = normalize_password(req.password)
    if not user or not verify_password(password_plain, user.password_hash):
        return JSONResponse(status_code=401, content=ok(msg="unauthorized", code=401))

    if user.status != "ACTIVE":
        return JSONResponse(status_code=403, content=ok(msg="forbidden", code=403))

    if not is_app_client_allowed(user.role_type, req.app_client):
        if not (settings.environment != "production" and user.username == "admin"):
            return JSONResponse(status_code=403, content=ok(msg="forbidden", code=403))

    UserContext.set_user_id(str(user.id))
    UserContext.set_tenant_id(str(user.tenant_id))
    UserContext.set_role_type(str(user.role_type))
    try:
        access_token, refresh_token = await create_new_token_pair(db, user, req.app_client)
    finally:
        UserContext.reset()

    data = {
        "accessToken": access_token,
        "refreshToken": refresh_token,
        "userInfo": {"id": user.id, "roleType": user.role_type, "tenantId": user.tenant_id, "orgId": user.org_id, "username": user.username, "nickname": user.real_name or user.username},
    }
    return JSONResponse(status_code=200, content=ok(data=data))


@router.post("/api/v1/auth/sms/send")
@router.post("/auth/sms/send")
async def send_sms_code(req: SmsSendRequest):
    if not validate_app_client(req.app_client):
        return JSONResponse(status_code=400, content=ok(msg="invalid app_client", code=400))

    if req.scene not in ALLOWED_SMS_SCENES:
        return JSONResponse(status_code=400, content=ok(msg="invalid scene", code=400))

    if not _is_mobile_valid(req.mobile):
        return JSONResponse(status_code=400, content=ok(msg="invalid mobile", code=400))

    _cleanup_stores()
    limit_key = f"{req.app_client}:{req.scene}:{req.mobile}"
    now_ts = time.time()
    next_allowed = SMS_RATE_LIMIT_STORE.get(limit_key, 0)
    if next_allowed > now_ts:
        retry_after = max(1, int(next_allowed - now_ts))
        return JSONResponse(
            status_code=429,
            content=ok(
                msg="sms request too frequent",
                code=429,
                data={"retryAfterSeconds": retry_after},
            ),
        )

    biz_no = f"sms_{int(now_ts)}_{uuid4().hex[:8]}"
    sms_code = "123456" if settings.environment != "production" else f"{uuid4().int % 1000000:06d}"
    SMS_CODE_STORE[biz_no] = {
        "mobile": req.mobile,
        "scene": req.scene,
        "app_client": req.app_client,
        "code": sms_code,
        "expire_at": now_ts + SMS_CODE_EXPIRE_SECONDS,
        "verify_attempts": 0,
    }
    SMS_RATE_LIMIT_STORE[limit_key] = now_ts + SMS_RETRY_AFTER_SECONDS

    return JSONResponse(
        status_code=200,
        content=ok(
            data={
                "bizNo": biz_no,
                "expireSeconds": SMS_CODE_EXPIRE_SECONDS,
                "retryAfterSeconds": SMS_RETRY_AFTER_SECONDS,
            }
        ),
    )


@router.post("/api/v1/auth/login/sms")
@router.post("/auth/login/sms")
async def login_by_sms(req: SmsLoginRequest, db: AsyncSession = Depends(get_db)):
    if not validate_app_client(req.app_client):
        return JSONResponse(status_code=400, content=ok(msg="invalid app_client", code=400))

    if not _is_mobile_valid(req.mobile):
        return JSONResponse(status_code=400, content=ok(msg="invalid mobile", code=400))

    verify_error = _verify_sms_code(req.mobile, req.code, req.bizNo, scene="LOGIN")
    if verify_error:
        return verify_error

    with system_mode_scope():
        user = (
            await db.execute(select(UserModel).where(UserModel.mobile == req.mobile).order_by(UserModel.id.asc()))
        ).scalars().first()

    if not user:
        return JSONResponse(status_code=404, content=ok(msg="user not found", code=404))

    if user.status != "ACTIVE":
        return JSONResponse(status_code=403, content=ok(msg="forbidden", code=403))

    if not is_app_client_allowed(user.role_type, req.app_client):
        if not (settings.environment != "production" and user.username == "admin"):
            return JSONResponse(status_code=403, content=ok(msg="forbidden", code=403))

    UserContext.set_user_id(str(user.id))
    UserContext.set_tenant_id(str(user.tenant_id))
    UserContext.set_role_type(str(user.role_type))
    try:
        access_token, refresh_token = await create_new_token_pair(db, user, req.app_client)
    finally:
        UserContext.reset()

    return JSONResponse(
        status_code=200,
        content=ok(
            data={
                "accessToken": access_token,
                "refreshToken": refresh_token,
                "userInfo": {"id": user.id, "roleType": user.role_type, "tenantId": user.tenant_id, "orgId": user.org_id, "username": user.username, "nickname": user.real_name or user.username},
            }
        ),
    )


@router.post("/api/v1/auth/register")
@router.post("/auth/register")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    if not validate_app_client(req.app_client):
        return JSONResponse(status_code=400, content=ok(msg="invalid app_client", code=400))

    if not req.app_client.startswith("reg_"):
        return JSONResponse(status_code=403, content=ok(msg="forbidden", code=403))

    if not _is_mobile_valid(req.mobile):
        return JSONResponse(status_code=400, content=ok(msg="invalid mobile", code=400))

    if not _is_invite_code_valid(req.inviteCode):
        return JSONResponse(status_code=400, content=ok(msg="invalid invite code", code=400))

    password_plain = normalize_password(req.password)
    if not _is_password_valid(password_plain):
        return JSONResponse(status_code=400, content=ok(msg="invalid password", code=400))

    verify_error = _verify_sms_code(req.mobile, req.code, req.bizNo, scene="REGISTER")
    if verify_error:
        return verify_error

    with system_mode_scope():
        tenant_id, org_id = await ensure_default_tenant_and_org(
            db,
            settings.default_tenant_id,
            settings.default_org_id,
        )
        existing_mobile = (
            await db.execute(
                select(UserModel).where(
                    UserModel.tenant_id == tenant_id,
                    UserModel.mobile == req.mobile,
                )
            )
        ).scalar_one_or_none()
        if existing_mobile:
            return JSONResponse(status_code=409, content=ok(msg="mobile already registered", code=409))

        username = req.mobile
        username_exists = (
            await db.execute(
                select(UserModel.id).where(
                    UserModel.tenant_id == tenant_id,
                    UserModel.username == username,
                )
            )
        ).scalar_one_or_none()
        if username_exists:
            username = f"{req.mobile}_{uuid4().hex[:6]}"

        user = UserModel(
            tenant_id=tenant_id,
            org_id=org_id,
            username=username,
            real_name=None,
            email=None,
            mobile=req.mobile,
            password_hash=hash_password(password_plain),
            role_type="REGULATOR",
            status="ACTIVE",
            token_version=1,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return JSONResponse(status_code=200, content=ok(data={"userId": user.id}))


@router.post("/api/v1/auth/password/verify-code")
@router.post("/auth/password/verify-code")
async def verify_password_code(req: PasswordVerifyCodeRequest, db: AsyncSession = Depends(get_db)):
    if not validate_app_client(req.app_client):
        return JSONResponse(status_code=400, content=ok(msg="invalid app_client", code=400))

    if not _is_mobile_valid(req.mobile):
        return JSONResponse(status_code=400, content=ok(msg="invalid mobile", code=400))

    verify_error = _verify_sms_code(req.mobile, req.code, req.bizNo, scene="RESET_PASSWORD")
    if verify_error:
        return verify_error

    with system_mode_scope():
        user = (
            await db.execute(select(UserModel).where(UserModel.mobile == req.mobile).order_by(UserModel.id.asc()))
        ).scalars().first()
    if not user:
        return JSONResponse(status_code=404, content=ok(msg="user not found", code=404))

    _cleanup_stores()
    reset_token = f"reset_{uuid4().hex}"
    RESET_TOKEN_STORE[reset_token] = {
        "user_id": user.id,
        "mobile": req.mobile,
        "app_client": req.app_client,
        "expire_at": time.time() + RESET_TOKEN_EXPIRE_SECONDS,
        "used": False,
    }
    return JSONResponse(
        status_code=200,
        content=ok(data={"resetToken": reset_token, "expireSeconds": RESET_TOKEN_EXPIRE_SECONDS}),
    )


@router.post("/api/v1/auth/password/reset")
@router.post("/auth/password/reset")
async def reset_password(req: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    if not validate_app_client(req.app_client):
        return JSONResponse(status_code=400, content=ok(msg="invalid app_client", code=400))

    if not _is_mobile_valid(req.mobile):
        return JSONResponse(status_code=400, content=ok(msg="invalid mobile", code=400))

    password_plain = normalize_password(req.newPassword)
    if not _is_password_valid(password_plain):
        return JSONResponse(status_code=400, content=ok(msg="invalid password", code=400))

    _cleanup_stores()
    token_payload = RESET_TOKEN_STORE.get(req.resetToken)
    if not token_payload:
        return JSONResponse(status_code=401, content=ok(msg="unauthorized", code=401))

    if token_payload.get("mobile") != req.mobile or token_payload.get("app_client") != req.app_client:
        return JSONResponse(status_code=401, content=ok(msg="unauthorized", code=401))

    if float(token_payload.get("expire_at", 0)) < time.time():
        RESET_TOKEN_STORE.pop(req.resetToken, None)
        return JSONResponse(status_code=400, content=ok(msg="verification code expired", code=46002))

    if bool(token_payload.get("used")):
        return JSONResponse(status_code=401, content=ok(msg="unauthorized", code=401))

    with system_mode_scope():
        user = await db.get(UserModel, int(token_payload["user_id"]))
        if not user or user.mobile != req.mobile:
            return JSONResponse(status_code=404, content=ok(msg="user not found", code=404))

        user.password_hash = hash_password(password_plain)
        user.token_version += 1
        await db.commit()

    token_payload["used"] = True
    return JSONResponse(status_code=200, content=ok(data={"updated": True}))


@router.get("/api/v1/auth/me")
@router.get("/auth/me")
async def me(user: UserModel = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.modules.user.models import Org as OrgModel2, Role as RoleModel2

    org_name = None
    if user.org_id:
        org = (await db.execute(select(OrgModel2).where(OrgModel2.id == user.org_id))).scalar_one_or_none()
        if org:
            org_name = org.name

    role_name = None
    if user.role_id:
        role = (await db.execute(select(RoleModel2).where(RoleModel2.id == user.role_id))).scalar_one_or_none()
        if role:
            role_name = role.name

    return JSONResponse(
        status_code=200,
        content=ok(
            data={
                "id": user.id,
                "username": user.username,
                "realName": user.real_name,
                "mobile": user.mobile,
                "gender": user.gender,
                "birthday": user.birthday,
                "email": user.email,
                "canteenScope": user.canteen_scope,
                "orgId": user.org_id,
                "orgName": org_name,
                "roleId": user.role_id,
                "roleName": role_name,
                "roleType": user.role_type,
                "tenantId": user.tenant_id,
                "status": user.status,
            }
        ),
    )


@router.put("/api/v1/auth/password")
@router.put("/auth/password")
async def change_password(req: PasswordChangeRequest, user: UserModel = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    old_password_plain = normalize_password(req.oldPassword)
    if not verify_password(old_password_plain, user.password_hash):
        return JSONResponse(status_code=400, content=ok(msg="incorrect old password", code=400))

    new_password_plain = normalize_password(req.newPassword)
    if not _is_password_valid(new_password_plain):
        return JSONResponse(status_code=400, content=ok(msg="invalid password", code=400))

    if req.oldPassword == req.newPassword:
        return JSONResponse(status_code=400, content=ok(msg="new password cannot be the same as old password", code=400))

    user.password_hash = hash_password(new_password_plain)
    user.token_version += 1
    await db.commit()

    return JSONResponse(status_code=200, content=ok(data={"updated": True}))


@router.post("/api/v1/auth/logout")
@router.post("/auth/logout")
async def logout(
    req: LogoutRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user),
):
    app_client = request.headers.get("X-App-Client")
    if not app_client:
        return JSONResponse(status_code=403, content=ok(msg="forbidden", code=403))

    try:
        claims = decode_refresh_token(req.refreshToken, app_client)
    except (ValueError, InvalidTokenError):
        return JSONResponse(status_code=401, content=ok(msg="unauthorized", code=401))

    if int(claims.get("uid", 0)) != user.id:
        return JSONResponse(status_code=403, content=ok(msg="forbidden", code=403))

    if int(claims.get("tenantId", 0)) != user.tenant_id:
        return JSONResponse(status_code=403, content=ok(msg="forbidden", code=403))

    if claims.get("appClient") != app_client:
        return JSONResponse(status_code=403, content=ok(msg="forbidden", code=403))

    token_jti = claims.get("jti")
    if not token_jti:
        return JSONResponse(status_code=401, content=ok(msg="unauthorized", code=401))

    await db.execute(
        update(RefreshTokenModel)
        .where(
            RefreshTokenModel.user_id == user.id,
            RefreshTokenModel.tenant_id == user.tenant_id,
            RefreshTokenModel.app_client == app_client,
            RefreshTokenModel.jti.in_([hash_jti(str(token_jti)), str(token_jti)]),
            RefreshTokenModel.revoked_at.is_(None),
        )
        .values(revoked_at=_utcnow())
    )

    await db.execute(
        update(UserModel)
        .where(UserModel.id == user.id, UserModel.tenant_id == user.tenant_id)
        .values(token_version=user.token_version + 1)
    )
    await db.commit()

    return JSONResponse(status_code=200, content=ok(data={"ok": True}))


@router.get("/api/v1/auth/me/permissions")
@router.get("/auth/me/permissions")
async def me_permissions(user: UserModel = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    data = await get_permissions_for_user(db, user)
    return JSONResponse(status_code=200, content=ok(data=data))


@router.put("/user/{user_id}/status")
async def update_user_status(
    user_id: int, req: StatusUpdateRequest, db: AsyncSession = Depends(get_db), _user: UserModel = Depends(get_current_user)
):
    permissions = await get_permissions_for_user(db, _user)
    if "user:status:update" not in permissions:
        return JSONResponse(status_code=403, content=ok(msg="forbidden", code=403))

    user = await get_user_by_id(db, user_id)
    if not user:
        return JSONResponse(status_code=400, content=ok(msg="invalid user", code=400))

    if req.status not in ALLOWED_STATUSES:
        return JSONResponse(status_code=400, content=ok(msg="invalid status", code=400))

    if user.status != req.status:
        user.status = req.status
        if user.status == "DISABLED":
            user.token_version += 1
        await db.commit()

    data = {"id": user.id, "status": user.status, "tokenVersion": user.token_version}
    return JSONResponse(status_code=200, content=ok(data=data))


@router.post("/api/v1/auth/refresh")
@router.post("/auth/refresh")
async def refresh(req: RefreshRequest, request: Request, db: AsyncSession = Depends(get_db)):
    app_client_header = request.headers.get("X-App-Client")
    if not app_client_header:
        return JSONResponse(status_code=403, content=ok(msg="forbidden", code=403))

    try:
        claims = decode_refresh_token(req.refreshToken, app_client_header)
    except (ValueError, InvalidTokenError):
        return JSONResponse(status_code=401, content=ok(msg="unauthorized", code=401))

    if claims.get("type") != "refresh":
        return JSONResponse(status_code=401, content=ok(msg="unauthorized", code=401))

    uid = claims.get("uid")
    tenant_id = claims.get("tenantId")
    if uid is None or tenant_id is None:
        return JSONResponse(status_code=401, content=ok(msg="unauthorized", code=401))

    UserContext.set_user_id(str(uid))
    UserContext.set_tenant_id(str(tenant_id))
    UserContext.set_role_type(str(claims.get("roleType") or ""))
    try:
        user = await get_user_by_id(db, int(uid))
        if not user or user.status != "ACTIVE":
            return JSONResponse(status_code=403, content=ok(msg="forbidden", code=403))

        if user.tenant_id != int(claims.get("tenantId", 0)):
            return JSONResponse(status_code=403, content=ok(msg="forbidden", code=403))

        if user.token_version != int(claims.get("tokenVersion", 0)):
            return JSONResponse(status_code=403, content=ok(msg="forbidden", code=403))

        app_client = claims.get("appClient")
        if not app_client or not validate_app_client(app_client):
            return JSONResponse(status_code=401, content=ok(msg="unauthorized", code=401))

        if app_client_header != app_client:
            return JSONResponse(status_code=403, content=ok(msg="forbidden", code=403))

        if not is_app_client_allowed(user.role_type, app_client):
            if not (settings.environment != "production" and user.username == "admin"):
                return JSONResponse(status_code=403, content=ok(msg="forbidden", code=403))

        token_jti = claims.get("jti")
        if not token_jti:
            return JSONResponse(status_code=401, content=ok(msg="unauthorized", code=401))

        access_token, refresh_token = await rotate_refresh_token(db, user, app_client, token_jti)
        if not access_token:
             return JSONResponse(status_code=401, content=ok(msg="invalid or expired token", code=401))

        return JSONResponse(
            status_code=200,
            content=ok(data={"accessToken": access_token, "refreshToken": refresh_token}),
        )
    finally:
        UserContext.reset()



@router.post("/api/v1/auth/idp/mock-login")
@router.post("/auth/idp/mock-login")
async def mock_login(req: MockLoginRequest, db: AsyncSession = Depends(get_db)):
    if settings.environment == "production":
        return JSONResponse(status_code=404, content=ok(msg="not found", code=404))

    if not validate_app_client(req.app_client):
        return JSONResponse(status_code=400, content=ok(msg="invalid app_client", code=400))

    adapter = MockIdpAdapter()
    identity = adapter.exchange(req)

    user = await get_user_by_external(db, identity.issuer, identity.sub)
    # Mock login: 允许未验证邮箱的账户链接
    email_verified = identity.raw_claims.get("email_verified") is True
    if not user and identity.email:
        tenant_id = settings.default_tenant_id or 1
        user = await get_user_by_email(db, identity.email, tenant_id)
        if user:
            await link_external_identity(db, user, identity)
            await db.commit()
    if not user:
        # Mock login: 直接创建用户，不经过严格安全检�?
        import hashlib
        from uuid import uuid4
        from app.core.security import hash_password
        
        role_type = "EXECUTOR"
        if req.app_client.startswith("reg_"):
            role_type = "REGULATOR"
        username_hash = hashlib.sha256(f"{identity.issuer}|{identity.sub}".encode("utf-8")).hexdigest()
        tenant_id = settings.default_tenant_id or 1
        org_id = settings.default_org_id or 1
        
        from app.modules.user.service import ensure_default_tenant_and_org
        tenant_id, org_id = await ensure_default_tenant_and_org(db, tenant_id, org_id)
        
        user = UserModel(
            tenant_id=tenant_id,
            org_id=org_id,
            username=f"idp_{username_hash[:32]}",
            real_name=identity.name,
            email=identity.email,
            mobile=None,
            password_hash=hash_password(str(uuid4())),
            role_type=role_type,
            status="ACTIVE",
            token_version=1,
        )
        db.add(user)
        await db.flush()
        
        from app.modules.user.models import ExternalIdentity as ExternalIdentityModel
        external = ExternalIdentityModel(
            user_id=user.id,
            issuer=identity.issuer,
            subject=identity.sub,
            name=identity.name,
            email=identity.email,
            raw_claims=identity.raw_claims,
        )
        db.add(external)
        
        from app.modules.user.models import Role as RoleModel, UserRole as UserRoleModel
        role = (await db.execute(
            select(RoleModel).where(RoleModel.tenant_id == user.tenant_id, RoleModel.role_type == role_type)
        )).scalar_one_or_none()
        if role:
            db.add(UserRoleModel(user_id=user.id, role_id=role.id, tenant_id=user.tenant_id))
        
        await db.commit()
        await db.refresh(user)

    if user.status != "ACTIVE":
        return JSONResponse(status_code=403, content=ok(msg="forbidden", code=403))

    if not is_app_client_allowed(user.role_type, req.app_client):
        if not (settings.environment != "production" and user.username == "admin"):
            return JSONResponse(status_code=403, content=ok(msg="forbidden", code=403))

    UserContext.set_user_id(str(user.id))
    UserContext.set_tenant_id(str(user.tenant_id))
    UserContext.set_role_type(str(user.role_type))
    try:
        access_token, refresh_token = await create_new_token_pair(db, user, req.app_client)
    finally:
        UserContext.reset()

    data = {
        "accessToken": access_token,
        "refreshToken": refresh_token,
        "userInfo": {"id": user.id, "roleType": user.role_type, "tenantId": user.tenant_id, "orgId": user.org_id, "username": user.username, "nickname": user.real_name or user.username},
    }
    return JSONResponse(status_code=200, content=ok(data=data))


# ══════════════════════════════════════════════════════════════════�?
# Admin: 用户 CRUD  (/admin/users)
# ══════════════════════════════════════════════════════════════════�?

@router.get("/admin/users")
async def admin_list_users(
    page: int = 1,
    size: int = 10,
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _user: UserModel = Depends(get_current_user),
):
    denied = _ensure_regulator(_user)
    if denied is not None:
        return denied

    from sqlalchemy import select, func
    from app.modules.user.models import Org as OrgModel2, Role as RoleModel2, UserRole as UserRoleModel2
    stmt = select(UserModel)
    if keyword:
        stmt = stmt.where(
            (UserModel.username.ilike(f"%{keyword}%")) |
            (UserModel.real_name.ilike(f"%{keyword}%"))
        )
    total_result = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = total_result.scalar_one()
    users = (await db.execute(stmt.offset((page - 1) * size).limit(size))).scalars().all()
    # batch load org names and role names
    org_ids = list({u.org_id for u in users if u.org_id})
    user_ids = [u.id for u in users]
    org_map: dict = {}
    role_map: dict = {}
    user_roles_map: dict = {}
    
    if org_ids:
        orgs = (await db.execute(select(OrgModel2).where(OrgModel2.id.in_(org_ids)))).scalars().all()
        org_map = {o.id: o.name for o in orgs}
    
    if user_ids:
        user_roles = (await db.execute(
            select(UserRoleModel2).where(UserRoleModel2.user_id.in_(user_ids))
        )).scalars().all()
        
        role_ids = list({ur.role_id for ur in user_roles})
        if role_ids:
            roles = (await db.execute(select(RoleModel2).where(RoleModel2.id.in_(role_ids)))).scalars().all()
            role_map = {r.id: r.name for r in roles}
        
        for ur in user_roles:
            if ur.user_id not in user_roles_map:
                user_roles_map[ur.user_id] = []
            user_roles_map[ur.user_id].append({
                "role_id": ur.role_id,
                "role_name": role_map.get(ur.role_id)
            })
    
    records = [
        {
            "id": u.id,
            "username": u.username,
            "real_name": u.real_name,
            "mobile": u.mobile,
            "gender": u.gender,
            "birthday": u.birthday,
            "canteen_scope": u.canteen_scope,
            "role_type": u.role_type,
            "roles": user_roles_map.get(u.id, []),
            "role_id": user_roles_map.get(u.id, [{}])[0].get("role_id") if user_roles_map.get(u.id) else None,
            "role_name": user_roles_map.get(u.id, [{}])[0].get("role_name") if user_roles_map.get(u.id) else None,
            "status": u.status,
            "org_id": u.org_id,
            "org_name": org_map.get(u.org_id) if u.org_id else None,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]
    return JSONResponse(status_code=200, content=ok(data={"total": total, "page": page, "size": size, "records": records}))


@router.post("/admin/users")
async def admin_create_user(
    req: UserAdminCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    denied = _ensure_regulator(current_user)
    if denied is not None:
        return denied

    from sqlalchemy import select
    from app.core.security import hash_password
    existing = (await db.execute(
        select(UserModel).where(
            UserModel.username == req.username,
            UserModel.tenant_id == current_user.tenant_id,
        )
    )).scalar_one_or_none()
    if existing:
        return JSONResponse(status_code=400, content=ok(msg="username already exists", code=400))
    user = UserModel(
        tenant_id=current_user.tenant_id,
        org_id=req.org_id,
        username=req.username,
        real_name=req.real_name,
        mobile=req.mobile,
        gender=req.gender,
        birthday=req.birthday,
        canteen_scope=req.canteen_scope,
        face_image_url=req.face_image_url,
        health_image_url=req.health_image_url,
        password_hash=hash_password(req.password),
        role_type=req.role_type,
        status="ACTIVE",
        token_version=1,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    if req.role_ids:
        await assign_roles_to_user(db, user.id, req.role_ids, current_user.tenant_id)
    
    return JSONResponse(status_code=200, content=ok(data={
        "id": user.id, "username": user.username, "role_type": user.role_type, "status": user.status
    }))


@router.put("/admin/users/{user_id}")
async def admin_update_user(
    user_id: int,
    req: UserAdminUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    denied = _ensure_regulator(current_user)
    if denied is not None:
        return denied

    from sqlalchemy import select, update as sql_update
    user = (await db.execute(
        select(UserModel).where(UserModel.id == user_id, UserModel.tenant_id == current_user.tenant_id)
    )).scalar_one_or_none()
    if not user:
        return JSONResponse(status_code=404, content=ok(msg="user not found", code=404))
    values: dict = {}
    if req.real_name is not None:
        values["real_name"] = req.real_name
    if req.mobile is not None:
        values["mobile"] = req.mobile
    if req.org_id is not None:
        values["org_id"] = req.org_id
    if req.gender is not None:
        values["gender"] = req.gender
    if req.birthday is not None:
        values["birthday"] = req.birthday
    if req.canteen_scope is not None:
        values["canteen_scope"] = req.canteen_scope
    if req.status is not None:
        if user.status != req.status and req.status == "DISABLED":
            values["token_version"] = user.token_version + 1
        values["status"] = req.status
    if req.face_image_url is not None:
        values["face_image_url"] = req.face_image_url
    if req.health_image_url is not None:
        values["health_image_url"] = req.health_image_url
    if values:
        await db.execute(
            sql_update(UserModel)
            .where(UserModel.id == user_id, UserModel.tenant_id == current_user.tenant_id)
            .values(**values)
        )
    
    if req.role_ids is not None:
        await remove_roles_from_user(db, user_id, await get_roles_for_user(db, user_id, current_user.tenant_id), current_user.tenant_id)
        if req.role_ids:
            await assign_roles_to_user(db, user_id, req.role_ids, current_user.tenant_id)
    
    await db.commit()
    return JSONResponse(status_code=200, content=ok(data={"id": user_id}))


@router.delete("/admin/users/{user_id}")
async def admin_delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    denied = _ensure_regulator(current_user)
    if denied is not None:
        return denied

    from sqlalchemy import select, delete as sql_delete
    from app.modules.user.models import UserRole as UserRoleModel2
    user = (await db.execute(
        select(UserModel).where(UserModel.id == user_id, UserModel.tenant_id == current_user.tenant_id)
    )).scalar_one_or_none()
    if not user:
        return JSONResponse(status_code=404, content=ok(msg="user not found", code=404))
    if user.id == current_user.id:
        return JSONResponse(status_code=400, content=ok(msg="cannot delete yourself", code=400))
    
    await db.execute(
        sql_delete(UserRoleModel2).where(UserRoleModel2.user_id == user_id)
    )
    await db.execute(
        sql_delete(UserModel)
        .where(UserModel.id == user_id, UserModel.tenant_id == current_user.tenant_id)
    )
    await db.commit()
    return JSONResponse(status_code=200, content=ok(data={"id": user_id}))


# ══════════════════════════════════════════════════════════════════�?
# 执行端：用户 CRUD  (/users, /user)
# ══════════════════════════════════════════════════════════════════�?

@router.post("/admin/users/{user_id}/reset-password")
async def admin_reset_user_password(
    user_id: int,
    req: AdminPasswordResetRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """监管端管理员重置指定用户密码。"""
    denied = _ensure_regulator(current_user)
    if denied is not None:
        return denied

    from sqlalchemy import select, update as sql_update
    from app.core.security import hash_password as _hash_pw

    user = (await db.execute(
        select(UserModel).where(
            UserModel.id == user_id,
            UserModel.tenant_id == current_user.tenant_id,
        )
    )).scalar_one_or_none()
    if not user:
        return JSONResponse(status_code=404, content=ok(msg="用户不存在", code=404))

    await db.execute(
        sql_update(UserModel)
        .where(UserModel.id == user_id, UserModel.tenant_id == current_user.tenant_id)
        .values(
            password_hash=_hash_pw(req.new_password),
            token_version=UserModel.token_version + 1,
        )
    )
    await db.commit()
    return JSONResponse(status_code=200, content=ok(data={"id": user_id}))


@router.get("/users")
async def list_users(
    page: int = 1,
    size: int = 10,
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _user: UserModel = Depends(get_current_user),
):
    from sqlalchemy import select, func
    from app.modules.user.models import Role as RoleModel2, UserRole as UserRoleModel2
    stmt = select(UserModel).where(UserModel.role_type == "EXECUTOR")
    if keyword:
        stmt = stmt.where(
            (UserModel.username.ilike(f"%{keyword}%")) |
            (UserModel.real_name.ilike(f"%{keyword}%"))
        )
    total_result = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = total_result.scalar_one()
    users = (await db.execute(stmt.offset((page - 1) * size).limit(size))).scalars().all()
    
    user_ids = [u.id for u in users]
    user_roles_map = {}
    role_map = {}
    
    if user_ids:
        user_roles = (await db.execute(
            select(UserRoleModel2).where(UserRoleModel2.user_id.in_(user_ids))
        )).scalars().all()
        
        role_ids = list({ur.role_id for ur in user_roles})
        if role_ids:
            roles = (await db.execute(select(RoleModel2).where(RoleModel2.id.in_(role_ids)))).scalars().all()
            role_map = {r.id: r.name for r in roles}
        
        for ur in user_roles:
            if ur.user_id not in user_roles_map:
                user_roles_map[ur.user_id] = []
            user_roles_map[ur.user_id].append({
                "role_id": ur.role_id,
                "role_name": role_map.get(ur.role_id)
            })
    
    records = [
        {
            "id": u.id, "username": u.username, "realName": u.real_name,
            "mobile": u.mobile, "status": 1 if u.status == "ACTIVE" else 0,
            "roleType": u.role_type,
            "roles": user_roles_map.get(u.id, []),
            "faceImage": u.face_image_url or "",
            "healthImage": u.health_image_url or "",
        }
        for u in users
    ]
    return JSONResponse(status_code=200, content=ok(data={"total": total, "records": records}))


@router.post("/user")
async def create_user_exec(
    req: UserAdminCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    from sqlalchemy import select
    from app.core.security import hash_password
    existing = (await db.execute(
        select(UserModel).where(
            UserModel.username == req.username,
            UserModel.tenant_id == current_user.tenant_id,
        )
    )).scalar_one_or_none()
    if existing:
        return JSONResponse(status_code=400, content=ok(msg="username already exists", code=400))
    user = UserModel(
        tenant_id=current_user.tenant_id,
        org_id=req.org_id,
        username=req.username,
        real_name=req.real_name,
        mobile=req.mobile,
        face_image_url=req.face_image_url,
        health_image_url=req.health_image_url,
        password_hash=hash_password(req.password),
        role_type="EXECUTOR",
        status="ACTIVE",
        token_version=1,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    if req.role_ids:
        await assign_roles_to_user(db, user.id, req.role_ids, current_user.tenant_id)
    
    return JSONResponse(status_code=200, content=ok(data={"id": user.id, "username": user.username}))


@router.put("/user")
async def update_user_exec(
    req: UserAdminUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    from sqlalchemy import update as sql_update
    values: dict = {}
    if req.mobile is not None:
        values["mobile"] = req.mobile
    if req.real_name is not None:
        values["real_name"] = req.real_name
    if req.org_id is not None:
        values["org_id"] = req.org_id
    if req.face_image_url is not None:
        values["face_image_url"] = req.face_image_url
    if req.health_image_url is not None:
        values["health_image_url"] = req.health_image_url
    if values:
        await db.execute(
            sql_update(UserModel)
            .where(UserModel.id == current_user.id, UserModel.tenant_id == current_user.tenant_id)
            .values(**values)
        )
    
    if req.role_ids is not None:
        await remove_roles_from_user(db, current_user.id, await get_roles_for_user(db, current_user.id, current_user.tenant_id), current_user.tenant_id)
        if req.role_ids:
            await assign_roles_to_user(db, current_user.id, req.role_ids, current_user.tenant_id)
    
    await db.commit()
    return JSONResponse(status_code=200, content=ok(data={"id": current_user.id}))


@router.delete("/user/{user_id}")
async def delete_user_exec(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    from sqlalchemy import select, delete as sql_delete
    from app.modules.user.models import UserRole as UserRoleModel2
    
    if user_id == current_user.id:
        return JSONResponse(status_code=400, content=ok(msg="cannot delete yourself", code=400))
    
    user = (await db.execute(
        select(UserModel).where(
            UserModel.id == user_id,
            UserModel.tenant_id == current_user.tenant_id,
            UserModel.role_type == "EXECUTOR"
        )
    )).scalar_one_or_none()
    if not user:
        return JSONResponse(status_code=404, content=ok(msg="user not found", code=404))
    
    await db.execute(
        sql_delete(UserRoleModel2).where(UserRoleModel2.user_id == user_id)
    )
    await db.execute(
        sql_delete(UserModel)
        .where(UserModel.id == user_id, UserModel.tenant_id == current_user.tenant_id)
    )
    await db.commit()
    return JSONResponse(status_code=200, content=ok(data={"id": user_id}))


# ══════════════════════════════════════════════════════════════════�?
# Admin: 角色 CRUD  (/admin/roles)
# ══════════════════════════════════════════════════════════════════�?

@router.get("/admin/roles")
async def admin_list_roles(
    page: int = 1,
    size: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    from sqlalchemy import select, func
    stmt = select(RoleModel).where(RoleModel.tenant_id == current_user.tenant_id)
    stmt = stmt.where(RoleModel.role_type == current_user.role_type)
    total_result = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = total_result.scalar_one()
    roles = (await db.execute(stmt.offset((page - 1) * size).limit(size))).scalars().all()
    
    role_ids = [r.id for r in roles]
    role_permissions_map = {}
    
    if role_ids:
        from app.modules.user.models import RolePermission as RolePermissionModel2
        role_permissions = (await db.execute(
            select(RolePermissionModel2).where(RolePermissionModel2.role_id.in_(role_ids))
        )).scalars().all()
        
        permission_ids = list({rp.permission_id for rp in role_permissions})
        if permission_ids:
            from app.modules.user.models import Permission as PermissionModel2
            permissions = (await db.execute(
                select(PermissionModel2).where(PermissionModel2.id.in_(permission_ids))
            )).scalars().all()
            permission_map = {p.id: p.code for p in permissions}
            
            for rp in role_permissions:
                if rp.role_id not in role_permissions_map:
                    role_permissions_map[rp.role_id] = []
                role_permissions_map[rp.role_id].append(permission_map.get(rp.permission_id))
    
    records = [
        {
            "id": r.id, "name": r.name, "role_type": r.role_type,
            "level": r.level, "permissions": role_permissions_map.get(r.id, []),
            "permissions_desc": r.permissions_desc or "",
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in roles
    ]
    return JSONResponse(status_code=200, content=ok(data={"total": total, "page": page, "size": size, "records": records}))


@router.post("/admin/roles")
async def admin_create_role(
    req: RoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    from app.core.constants.levels import LEVEL_PERMISSIONS
    
    if req.level and req.level not in LEVEL_PERMISSIONS:
        return JSONResponse(
            status_code=400,
            content=ok(msg=f"职级必须是以下值之一: {', '.join(LEVEL_PERMISSIONS.keys())}", code=400)
        )
    
    role = RoleModel(
        tenant_id=current_user.tenant_id,
        name=req.name,
        role_type=current_user.role_type,
        level=req.level,
        permissions_desc=req.permissions_desc,
    )
    db.add(role)
    await db.commit()
    await db.refresh(role)
    
    return JSONResponse(status_code=200, content=ok(data={"id": role.id, "name": role.name}))


@router.put("/admin/roles/{role_id}")
async def admin_update_role(
    role_id: int,
    req: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    from sqlalchemy import select
    from app.core.constants.levels import LEVEL_PERMISSIONS
    
    role = (await db.execute(
        select(RoleModel).where(RoleModel.id == role_id, RoleModel.tenant_id == current_user.tenant_id)
    )).scalar_one_or_none()
    if not role:
        return JSONResponse(status_code=404, content=ok(msg="role not found", code=404))
    
    if req.level is not None and req.level not in LEVEL_PERMISSIONS:
        return JSONResponse(
            status_code=400,
            content=ok(msg=f"职级必须是以下值之一: {', '.join(LEVEL_PERMISSIONS.keys())}", code=400)
        )
    
    from sqlalchemy import update as sql_update
    values = {}
    if req.name is not None:
        values["name"] = req.name
    if req.role_type is not None:
        values["role_type"] = req.role_type
    if req.level is not None:
        values["level"] = req.level
    if req.permissions_desc is not None:
        values["permissions_desc"] = req.permissions_desc
    if values:
        await db.execute(
            sql_update(RoleModel)
            .where(RoleModel.id == role_id, RoleModel.tenant_id == current_user.tenant_id)
            .values(**values)
        )
    
    await db.commit()
    return JSONResponse(status_code=200, content=ok(data={"id": role_id, "name": req.name or role.name}))


@router.delete("/admin/roles/{role_id}")
async def admin_delete_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    from sqlalchemy import select, delete as sql_delete
    from app.modules.user.models import RolePermission as RolePermissionModel2, UserRole as UserRoleModel2
    role = (await db.execute(
        select(RoleModel).where(RoleModel.id == role_id, RoleModel.tenant_id == current_user.tenant_id)
    )).scalar_one_or_none()
    if not role:
        return JSONResponse(status_code=404, content=ok(msg="role not found", code=404))
    
    await db.execute(
        sql_delete(RolePermissionModel2).where(RolePermissionModel2.role_id == role_id)
    )
    await db.execute(
        sql_delete(UserRoleModel2).where(UserRoleModel2.role_id == role_id)
    )
    await db.execute(
        sql_delete(RoleModel)
        .where(RoleModel.id == role_id, RoleModel.tenant_id == current_user.tenant_id)
    )
    await db.commit()
    return JSONResponse(status_code=200, content=ok(data={"id": role_id}))


@router.get("/admin/permissions")
async def admin_list_permissions(
    db: AsyncSession = Depends(get_db),
    _user: UserModel = Depends(get_current_user),
):
    from app.core.constants.permissions import PERMISSIONS_BY_MODULE
    permissions = await get_all_permissions(db)
    records = [
        {
            "id": p.id,
            "code": p.code,
            "name": p.name,
        }
        for p in permissions
    ]
    return JSONResponse(status_code=200, content=ok(data={"total": len(records), "records": records}))


@router.post("/admin/permissions/initialize")
async def admin_initialize_permissions(
    db: AsyncSession = Depends(get_db),
    _user: UserModel = Depends(get_current_user),
):
    permission_map = await initialize_permissions(db)
    return JSONResponse(status_code=200, content=ok(data={"count": len(permission_map)}))


@router.get("/admin/rbac/validate")
async def admin_validate_rbac_consistency(
    db: AsyncSession = Depends(get_db),
    _user: UserModel = Depends(get_current_user),
):
    result = await validate_rbac_consistency(db)
    return JSONResponse(status_code=200, content=ok(data=result))


@router.post("/admin/roles/{role_id}/permissions")
async def admin_assign_permissions_to_role(
    role_id: int,
    req: RolePermissionAssign,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    from sqlalchemy import select
    role = (await db.execute(
        select(RoleModel).where(RoleModel.id == role_id, RoleModel.tenant_id == current_user.tenant_id)
    )).scalar_one_or_none()
    if not role:
        return JSONResponse(status_code=404, content=ok(msg="role not found", code=404))
    
    await assign_permissions_to_role(db, role_id, req.permission_codes, current_user.tenant_id)
    return JSONResponse(status_code=200, content=ok(data={"role_id": role_id, "permissions": req.permission_codes}))


@router.delete("/admin/roles/{role_id}/permissions")
async def admin_remove_permissions_from_role(
    role_id: int,
    req: RolePermissionAssign,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    from sqlalchemy import select
    role = (await db.execute(
        select(RoleModel).where(RoleModel.id == role_id, RoleModel.tenant_id == current_user.tenant_id)
    )).scalar_one_or_none()
    if not role:
        return JSONResponse(status_code=404, content=ok(msg="role not found", code=404))
    
    await remove_permissions_from_role(db, role_id, req.permission_codes, current_user.tenant_id)
    return JSONResponse(status_code=200, content=ok(data={"role_id": role_id, "permissions": req.permission_codes}))


@router.get("/admin/roles/{role_id}/permissions")
async def admin_get_role_permissions(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    from sqlalchemy import select
    role = (await db.execute(
        select(RoleModel).where(RoleModel.id == role_id, RoleModel.tenant_id == current_user.tenant_id)
    )).scalar_one_or_none()
    if not role:
        return JSONResponse(status_code=404, content=ok(msg="role not found", code=404))
    
    permissions = await get_permissions_for_role(db, role_id, current_user.tenant_id)
    return JSONResponse(status_code=200, content=ok(data={"role_id": role_id, "permissions": permissions}))


@router.post("/admin/users/{user_id}/roles")
async def admin_assign_roles_to_user(
    user_id: int,
    req: UserRoleAssign,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    from sqlalchemy import select
    user = (await db.execute(
        select(UserModel).where(UserModel.id == user_id, UserModel.tenant_id == current_user.tenant_id)
    )).scalar_one_or_none()
    if not user:
        return JSONResponse(status_code=404, content=ok(msg="user not found", code=404))
    
    await assign_roles_to_user(db, user_id, req.role_ids, current_user.tenant_id)
    return JSONResponse(status_code=200, content=ok(data={"user_id": user_id, "role_ids": req.role_ids}))


@router.delete("/admin/users/{user_id}/roles")
async def admin_remove_roles_from_user(
    user_id: int,
    req: UserRoleAssign,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    from sqlalchemy import select
    user = (await db.execute(
        select(UserModel).where(UserModel.id == user_id, UserModel.tenant_id == current_user.tenant_id)
    )).scalar_one_or_none()
    if not user:
        return JSONResponse(status_code=404, content=ok(msg="user not found", code=404))
    
    await remove_roles_from_user(db, user_id, req.role_ids, current_user.tenant_id)
    return JSONResponse(status_code=200, content=ok(data={"user_id": user_id, "role_ids": req.role_ids}))


@router.get("/admin/users/{user_id}/roles")
async def admin_get_user_roles(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    from sqlalchemy import select
    user = (await db.execute(
        select(UserModel).where(UserModel.id == user_id, UserModel.tenant_id == current_user.tenant_id)
    )).scalar_one_or_none()
    if not user:
        return JSONResponse(status_code=404, content=ok(msg="user not found", code=404))
    
    role_ids = await get_roles_for_user(db, user_id, current_user.tenant_id)
    return JSONResponse(status_code=200, content=ok(data={"user_id": user_id, "role_ids": role_ids}))


# ══════════════════════════════════════════════════════════════════�?
# Admin: 部门(Org) CRUD  (/admin/depts)
# ══════════════════════════════════════════════════════════════════�?

@router.get("/admin/depts")
async def admin_list_depts(
    page: int = 1,
    size: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    from sqlalchemy import select, func
    stmt = select(OrgModel)
    total_result = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = total_result.scalar_one()
    orgs = (await db.execute(stmt.offset((page - 1) * size).limit(size))).scalars().all()
    org_ids = [o.id for o in orgs]
    member_count_map: dict = {}
    if org_ids:
        count_stmt = (
            select(UserModel.org_id, func.count(UserModel.id).label("cnt"))
            .where(UserModel.org_id.in_(org_ids))
            .group_by(UserModel.org_id)
        )
        count_rows = (await db.execute(count_stmt)).all()
        member_count_map = {row.org_id: row.cnt for row in count_rows}
    records = [
        {
            "id": o.id, "name": o.name, "parent_id": o.parent_id,
            "org_type": o.org_type, "tenant_id": o.tenant_id,
            "member_count": member_count_map.get(o.id, 0),
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in orgs
    ]
    return JSONResponse(status_code=200, content=ok(data={"total": total, "records": records}))


@router.post("/admin/depts")
async def admin_create_dept(
    req: OrgAdminCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    org = OrgModel(
        tenant_id=current_user.tenant_id,
        name=req.name,
        parent_id=req.parent_id,
        org_type=req.org_type,
    )
    db.add(org)
    await db.commit()
    await db.refresh(org)
    return JSONResponse(status_code=200, content=ok(data={"id": org.id, "name": org.name}))


@router.put("/admin/depts/{dept_id}")
async def admin_update_dept(
    dept_id: int,
    req: OrgAdminUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    from sqlalchemy import select, update as sql_update
    org = (await db.execute(
        select(OrgModel).where(OrgModel.id == dept_id, OrgModel.tenant_id == current_user.tenant_id)
    )).scalar_one_or_none()
    if not org:
        return JSONResponse(status_code=404, content=ok(msg="dept not found", code=404))
    values: dict = {}
    if req.name is not None:
        values["name"] = req.name
    if req.parent_id is not None:
        values["parent_id"] = req.parent_id
    if req.org_type is not None:
        values["org_type"] = req.org_type
    if values:
        await db.execute(
            sql_update(OrgModel)
            .where(OrgModel.id == dept_id, OrgModel.tenant_id == current_user.tenant_id)
            .values(**values)
        )
        await db.commit()
        if req.name is not None:
            org.name = req.name
    return JSONResponse(status_code=200, content=ok(data={"id": org.id, "name": org.name}))


@router.delete("/admin/depts/{dept_id}")
async def admin_delete_dept(
    dept_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    from sqlalchemy import select, delete as sql_delete
    org = (await db.execute(
        select(OrgModel).where(OrgModel.id == dept_id, OrgModel.tenant_id == current_user.tenant_id)
    )).scalar_one_or_none()
    if not org:
        return JSONResponse(status_code=404, content=ok(msg="dept not found", code=404))

    # Use an explicit tenant-scoped DELETE statement to satisfy security guard checks.
    await db.execute(
        sql_delete(OrgModel).where(OrgModel.id == dept_id, OrgModel.tenant_id == current_user.tenant_id)
    )
    await db.commit()
    return JSONResponse(status_code=200, content=ok(data={"id": dept_id}))


# ════════════════════════════════════════════════════════════════�?
# Admin: 菜单 CRUD  (/admin/menus)
# ════════════════════════════════════════════════════════════════�?

@router.get("/admin/menus")
async def admin_list_menus(
    db: AsyncSession = Depends(get_db),
    _user: UserModel = Depends(get_current_user),
):
    from sqlalchemy import select
    menus = (await db.execute(select(MenuModel).order_by(MenuModel.sort, MenuModel.id))).scalars().all()

    def build_tree(items, parent_id=None):
        result = []
        for m in items:
            if m.parent_id == parent_id:
                node = {
                    "id": m.id, "parent_id": m.parent_id, "name": m.name,
                    "path": m.path, "component": m.component, "sort": m.sort,
                    "hidden": bool(m.hidden),
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                children = build_tree(items, m.id)
                if children:
                    node["children"] = children
                result.append(node)
        return result

    tree = build_tree(menus)
    return JSONResponse(status_code=200, content=ok(data={"records": tree, "total": len(menus)}))


@router.post("/admin/menus")
async def admin_create_menu(
    req: MenuCreate,
    db: AsyncSession = Depends(get_db),
    _user: UserModel = Depends(get_current_user),
):
    menu = MenuModel(
        parent_id=req.parent_id,
        name=req.name,
        path=req.path,
        component=req.component,
        sort=req.sort,
        hidden=1 if req.hidden else 0,
    )
    db.add(menu)
    await db.commit()
    await db.refresh(menu)
    return JSONResponse(status_code=200, content=ok(data={"id": menu.id, "name": menu.name}))


@router.put("/admin/menus/{menu_id}")
async def admin_update_menu(
    menu_id: int,
    req: MenuUpdate,
    db: AsyncSession = Depends(get_db),
    _user: UserModel = Depends(get_current_user),
):
    from sqlalchemy import select
    menu = (await db.execute(select(MenuModel).where(MenuModel.id == menu_id))).scalar_one_or_none()
    if not menu:
        return JSONResponse(status_code=404, content=ok(msg="menu not found", code=404))
    if req.name is not None:
        menu.name = req.name
    if req.path is not None:
        menu.path = req.path
    if req.component is not None:
        menu.component = req.component
    if req.sort is not None:
        menu.sort = req.sort
    if req.hidden is not None:
        menu.hidden = 1 if req.hidden else 0
    if req.parent_id is not None:
        menu.parent_id = req.parent_id
    await db.commit()
    return JSONResponse(status_code=200, content=ok(data={"id": menu.id}))


@router.delete("/admin/menus/{menu_id}")
async def admin_delete_menu(
    menu_id: int,
    db: AsyncSession = Depends(get_db),
    _user: UserModel = Depends(get_current_user),
):
    from sqlalchemy import select
    menu = (await db.execute(select(MenuModel).where(MenuModel.id == menu_id))).scalar_one_or_none()
    if not menu:
        return JSONResponse(status_code=404, content=ok(msg="menu not found", code=404))
    await db.delete(menu)
    await db.commit()
    return JSONResponse(status_code=200, content=ok(data={"id": menu_id}))


async def oidc_login(req: OidcLoginRequest, db: AsyncSession = Depends(get_db)):
    if not validate_app_client(req.app_client):
        return JSONResponse(status_code=400, content=ok(msg="invalid app_client", code=400))
    if not settings.has_oidc:
        return JSONResponse(status_code=500, content=ok(msg="oidc not configured", code=500))
    try:
        identity = verify_id_token(req.id_token, req.nonce, req.max_auth_age)
    except Exception:
        return JSONResponse(status_code=401, content=ok(msg="unauthorized", code=401))

    with system_mode_scope():
        user = await get_user_by_external(db, identity.issuer, identity.sub)
        email_verified = identity.raw_claims.get("email_verified") is True
        if not user and identity.email and email_verified:
            tenant_id = settings.default_tenant_id or 1
            user = await get_user_by_email(db, identity.email, tenant_id)
            if user:
                await link_external_identity(db, user, identity)
        if not user:
            user = await create_user_from_external(db, identity, req.app_client)

    if user.status != "ACTIVE":
        return JSONResponse(status_code=403, content=ok(msg="forbidden", code=403))
    if not is_app_client_allowed(user.role_type, req.app_client):
        return JSONResponse(status_code=403, content=ok(msg="forbidden", code=403))

    UserContext.set_user_id(str(user.id))
    UserContext.set_tenant_id(str(user.tenant_id))
    UserContext.set_role_type(str(user.role_type))
    try:
        access_token, refresh_token = await create_new_token_pair(db, user, req.app_client)
    finally:
        UserContext.reset()

    data = {
        "accessToken": access_token,
        "refreshToken": refresh_token,
        "userInfo": {"id": user.id, "roleType": user.role_type, "tenantId": user.tenant_id, "orgId": user.org_id, "username": user.username, "nickname": user.real_name or user.username},
    }
    return JSONResponse(status_code=200, content=ok(data=data))

