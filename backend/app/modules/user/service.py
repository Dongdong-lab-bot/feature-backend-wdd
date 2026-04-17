import hashlib
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

import jwt
from jwt import PyJWKClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.core.config import get_settings
from app.core.events import TENANT_CREATED, publish
from app.core.security import hash_password, jwt_encode
from app.db.tenant_safe_executor import TenantSafeExecutor
from app.modules.user.models import (
    ExternalIdentity as ExternalIdentityModel,
    Org as OrgModel,
    Permission as PermissionModel,
    RefreshToken as RefreshTokenModel,
    Role as RoleModel,
    RolePermission as RolePermissionModel,
    Tenant as TenantModel,
    User as UserModel,
    UserRole as UserRoleModel,
)
from app.modules.user.schemas import ExternalIdentityPayload, OrgResponse

settings = get_settings()
logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def hash_jti(jti: str) -> str:
    return hashlib.sha256(jti.encode("utf-8")).hexdigest()


def make_access_token(user: UserModel, app_client: str) -> str:
    now = int(time.time())
    exp = now + settings.access_token_expire_minutes * 60
    payload = {
        "iss": settings.app_name,
        "aud": app_client,
        "uid": user.id,
        "tenantId": user.tenant_id,
        "roleType": user.role_type,
        "appClient": app_client,
        "tokenVersion": user.token_version,
        "iat": now,
        "exp": exp,
        "jti": str(uuid4()),
        "type": "access",
    }
    return jwt_encode(payload)


def make_refresh_token(user: UserModel, app_client: str, family_id: Optional[str] = None) -> Tuple[str, str, int, str]:
    now = int(time.time())
    exp = now + settings.refresh_token_expire_days * 24 * 60 * 60
    jti = str(uuid4())
    if not family_id:
        family_id = str(uuid4())
        
    payload = {
        "iss": settings.app_name,
        "aud": app_client,
        "uid": user.id,
        "tenantId": user.tenant_id,
        "roleType": user.role_type,
        "appClient": app_client,
        "tokenVersion": user.token_version,
        "iat": now,
        "exp": exp,
        "jti": jti,
        "type": "refresh",
    }
    return jwt_encode(payload), jti, exp, family_id


async def ensure_default_tenant_and_org(db: AsyncSession, tenant_id: int, org_id: int) -> Tuple[int, int]:
    org = await db.get(OrgModel, org_id)
    if org:
        tenant_id = org.tenant_id
        tenant = await db.get(TenantModel, tenant_id)
        if not tenant:
            db.add(TenantModel(id=tenant_id, name="default", status="ACTIVE"))
            await db.flush()
            publish(TENANT_CREATED, {"tenant_id": tenant_id, "admin_user_id": None, "created_at": _utcnow().isoformat()})
        return tenant_id, org_id
    tenant = await db.get(TenantModel, tenant_id)
    if not tenant:
        db.add(TenantModel(id=tenant_id, name="default", status="ACTIVE"))
        await db.flush()
        publish(TENANT_CREATED, {"tenant_id": tenant_id, "admin_user_id": None, "created_at": _utcnow().isoformat()})
    db.add(
        OrgModel(
            id=org_id,
            tenant_id=tenant_id,
            parent_id=None,
            name="默认机构",
            org_type="AREA",
            manager_id=None,
        )
    )
    await db.flush()
    return tenant_id, org_id


async def ensure_dev_admin_user(
    db: AsyncSession, username: str = "admin", password: str = "py427123"
) -> UserModel:
    tenant_id, org_id = await ensure_default_tenant_and_org(db, settings.default_tenant_id, settings.default_org_id)

    user = (
        await db.execute(
            select(UserModel).where(
                UserModel.tenant_id == tenant_id,
                UserModel.username == username,
            )
        )
    ).scalar_one_or_none()

    if not user:
        user = UserModel(
            tenant_id=tenant_id,
            org_id=org_id,
            username=username,
            real_name="管理员",
            email=None,
            mobile=None,
            password_hash=hash_password(password),
            role_type="REGULATOR",
            status="ACTIVE",
            token_version=1,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    await db.execute(
        update(UserModel)
        .where(UserModel.tenant_id == tenant_id, UserModel.username == username)
        .values(
            password_hash=hash_password(password),
            status="ACTIVE",
            role_type="REGULATOR",
            org_id=org_id,
        )
    )
    await db.commit()

    user = (
        await db.execute(
            select(UserModel).where(
                UserModel.tenant_id == tenant_id,
                UserModel.username == username,
            )
        )
    ).scalar_one()
    return user


async def create_user_from_external(
    db: AsyncSession, identity: ExternalIdentityPayload, app_client: str
) -> UserModel:
    # 安全策略：禁止自动创建 REGULATOR 角色
    if app_client.startswith("reg_"):
        raise ValueError("Regulator account cannot be auto-created via IDP")

    # 安全策略：要求 email 完成验证后才能创建账号
    if not identity.raw_claims.get("email_verified") and identity.email:
        logger.warning(f"Blocking account creation for unverified email: {identity.email}")
        raise ValueError("Email must be verified to create account")

    role_type = "EXECUTOR"
    username_hash = hashlib.sha256(f"{identity.issuer}|{identity.sub}".encode("utf-8")).hexdigest()
    tenant_id = settings.default_tenant_id or 1
    org_id = settings.default_org_id or 1
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
    external = ExternalIdentityModel(
        user_id=user.id,
        issuer=identity.issuer,
        subject=identity.sub,
        name=identity.name,
        email=identity.email,
        raw_claims=identity.raw_claims,
    )
    db.add(external)
    role = (await db.execute(
        select(RoleModel).where(RoleModel.tenant_id == user.tenant_id, RoleModel.role_type == role_type)
    )).scalar_one_or_none()
    if role:
        db.add(UserRoleModel(user_id=user.id, role_id=role.id, tenant_id=user.tenant_id))
    await db.commit()
    await db.refresh(user)
    return user


async def link_external_identity(db: AsyncSession, user: UserModel, identity: ExternalIdentityPayload) -> None:
    existing = (await db.execute(
        select(ExternalIdentityModel).where(
            ExternalIdentityModel.issuer == identity.issuer,
            ExternalIdentityModel.subject == identity.sub,
        )
    )).scalar_one_or_none()
    if existing:
        return
    db.add(
        ExternalIdentityModel(
            user_id=user.id,
            issuer=identity.issuer,
            subject=identity.sub,
            name=identity.name,
            email=identity.email,
            raw_claims=identity.raw_claims,
        )
    )
    await db.flush()


async def revoke_refresh_token_family(db: AsyncSession, family_id: str):
    now_dt = _utcnow()
    await db.execute(
        update(RefreshTokenModel)
        .where(RefreshTokenModel.family_id == family_id, RefreshTokenModel.revoked_at.is_(None))
        .values(revoked_at=now_dt)
    )
    await db.commit()


async def rotate_refresh_token(
    db: AsyncSession, user: UserModel, app_client: str, token_jti: str
) -> Tuple[Optional[str], Optional[str]]:
    now_dt = datetime.utcnow()
    
    # Find the token
    # NOTE: token_jti 明文兼容仅用于历史数据迁移
    token_row = (
        (await db.execute(
            select(RefreshTokenModel)
            .where(
                RefreshTokenModel.jti.in_([hash_jti(token_jti), token_jti]),
                RefreshTokenModel.user_id == user.id,
                RefreshTokenModel.tenant_id == user.tenant_id,
                RefreshTokenModel.app_client == app_client,
            )
            .with_for_update()
        ))
        .scalar_one_or_none()
    )

    if not token_row:
        return None, None

    # Reuse detection
    if token_row.revoked_at is not None:
        logger.warning(
            f"SECURITY: Refresh token reuse detected! User: {user.id}, Family: {token_row.family_id}, IP: (check logs)"
        )
        await revoke_refresh_token_family(db, token_row.family_id)
        return None, None

    if token_row.expires_at <= now_dt:
        return None, None

    # Normal rotation
    token_row.revoked_at = now_dt
    
    # Inherit family_id
    family_id = token_row.family_id
    
    refresh_token, refresh_jti, refresh_exp, _ = make_refresh_token(user, app_client, family_id=family_id)
    
    db.add(
        RefreshTokenModel(
            user_id=user.id,
            tenant_id=user.tenant_id,
            app_client=app_client,
            jti=hash_jti(refresh_jti),
            family_id=family_id,
            expires_at=datetime.utcfromtimestamp(refresh_exp),
        )
    )
    await db.commit()
    
    access_token = make_access_token(user, app_client)
    return access_token, refresh_token


async def create_new_token_pair(db: AsyncSession, user: UserModel, app_client: str) -> Tuple[str, str]:
    refresh_token, refresh_jti, refresh_exp, family_id = make_refresh_token(user, app_client)
    db.add(
        RefreshTokenModel(
            user_id=user.id,
            tenant_id=user.tenant_id,
            app_client=app_client,
            jti=hash_jti(refresh_jti),
            family_id=family_id,
            expires_at=datetime.utcfromtimestamp(refresh_exp),
        )
    )
    await db.commit()
    access_token = make_access_token(user, app_client)
    return access_token, refresh_token


def verify_id_token(id_token: str, nonce: str, max_auth_age: Optional[int]) -> ExternalIdentityPayload:
    jwks_client = PyJWKClient(settings.oidc_jwks_url)
    signing_key = jwks_client.get_signing_key_from_jwt(id_token)
    kwargs = {
        "key": signing_key.key,
        "algorithms": ["RS256"],
        "options": {"require": ["exp", "iat"]},
        "issuer": settings.oidc_issuer,
    }
    if settings.oidc_client_id:
        kwargs["audience"] = settings.oidc_client_id
    claims = jwt.decode(id_token, **kwargs)
    issuer = claims.get("iss")
    sub = claims.get("sub")
    if not issuer or not sub:
        raise ValueError("missing required claims")
    token_nonce = claims.get("nonce")
    if not token_nonce or token_nonce != nonce:
        raise ValueError("invalid nonce")
    auth_time = claims.get("auth_time")
    if auth_time is None:
        raise ValueError("missing auth_time")
    auth_time_value = int(auth_time)
    now = int(time.time())
    if auth_time_value > now:
        raise ValueError("invalid auth_time")
    if max_auth_age is not None and now - auth_time_value > max_auth_age:
        raise ValueError("auth_time expired")
    return ExternalIdentityPayload(
        issuer=str(issuer),
        sub=str(sub),
        name=claims.get("name"),
        email=claims.get("email"),
        raw_claims=claims,
    )


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[UserModel]:
    return (await db.execute(select(UserModel).where(UserModel.username == username))).scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str, tenant_id: int) -> Optional[UserModel]:
    return (await db.execute(
        select(UserModel).where(UserModel.email == email, UserModel.tenant_id == tenant_id)
    )).scalar_one_or_none()


async def get_user_by_external(db: AsyncSession, issuer: str, sub: str) -> Optional[UserModel]:
    external = (await db.execute(
        select(ExternalIdentityModel).where(
            ExternalIdentityModel.issuer == issuer, ExternalIdentityModel.subject == sub
        )
    )).scalar_one_or_none()
    if not external:
        return None
    return await db.get(UserModel, external.user_id)


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[UserModel]:
    return await db.get(UserModel, user_id)


async def get_permissions_for_user(db: AsyncSession, user: UserModel) -> list[str]:
    from app.core.constants.levels import LEVEL_PERMISSIONS
    
    role_ids = set()
    
    if user.role_id:
        role_ids.add(user.role_id)
    
    rows = await db.execute(
        select(UserRoleModel.role_id).where(
            UserRoleModel.user_id == user.id,
            UserRoleModel.tenant_id == user.tenant_id
        )
    )
    for row in rows:
        role_ids.add(row[0])
    
    if not role_ids:
        return []
    
    roles_result = await db.execute(
        select(RoleModel).where(RoleModel.id.in_(role_ids))
    )
    roles = roles_result.scalars().all()
    
    all_permissions = set()
    for role in roles:
        if role.level and role.level in LEVEL_PERMISSIONS:
            all_permissions.update(LEVEL_PERMISSIONS[role.level])
    
    return list(all_permissions)


async def get_org_tree_recursive(db: AsyncSession, root_id: int, tenant_id: int) -> Optional[OrgResponse]:
    """
    Fetch organization tree using SQLAlchemy CTE (Common Table Expressions).
    This avoids Python-level recursion and optimizes performance.
    """
    # 1. Base statement: Select the root node
    # Security: Strictly filter by tenant_id to prevent data leakage
    base_stmt = (
        select(OrgModel)
        .where(
            OrgModel.id == root_id,
            OrgModel.tenant_id == tenant_id,
            # OrgModel.status != "DISABLED" # Optional: based on requirements
        )
        .cte(name="org_tree", recursive=True)
    )

    # 2. Recursive part: Select children joining on parent_id
    org_alias = aliased(OrgModel)
    recursive_part = (
        select(org_alias)
        .where(org_alias.tenant_id == tenant_id)
        .join(base_stmt, org_alias.parent_id == base_stmt.c.id)
    )

    # 3. Union all
    org_cte = base_stmt.union_all(recursive_part)

    # 4. Final selection using tenant-safe executor
    records = await TenantSafeExecutor.execute_cte(
        db=db,
        model=OrgModel,
        cte_statement=select(org_cte),
        tenant_id=tenant_id
    )

    if not records:
        return None

    # 5. Build tree in memory (linear complexity O(N))
    nodes: Dict[int, OrgResponse] = {}
    for org in records:
        nodes[org.id] = OrgResponse(
            id=org.id,
            name=org.name,
            parent_id=org.parent_id,
            children=[],
        )

    root_node = nodes.get(root_id)
    
    # Link children to parents
    for node in nodes.values():
        if node.parent_id and node.parent_id in nodes:
            nodes[node.parent_id].children.append(node)

    return root_node


async def get_canteen_ids_by_tenant(db: AsyncSession, tenant_id: int) -> List[int]:
    rows = (
        await db.execute(
            select(OrgModel.id).where(
                OrgModel.tenant_id == tenant_id,
                OrgModel.org_type == "CANTEEN",
            )
        )
    ).scalars().all()
    return list(rows)


async def get_active_tenant_ids(db: AsyncSession) -> List[int]:
    rows = (
        await db.execute(
            select(TenantModel.id).where(TenantModel.status == "ACTIVE")
        )
    ).scalars().all()
    return list(rows)


async def initialize_permissions(db: AsyncSession) -> Dict[str, int]:
    from app.core.constants.permissions import PERMISSIONS_BY_MODULE
    
    permission_map = {}
    
    for module, permissions in PERMISSIONS_BY_MODULE.items():
        for permission_code in permissions:
            existing = await db.execute(
                select(PermissionModel).where(PermissionModel.code == permission_code)
            )
            existing_permission = existing.scalar_one_or_none()
            
            if not existing_permission:
                permission = PermissionModel(
                    code=permission_code,
                    name=permission_code
                )
                db.add(permission)
                await db.flush()
                permission_map[permission_code] = permission.id
            else:
                permission_map[permission_code] = existing_permission.id
    
    await db.commit()
    return permission_map


async def get_all_permissions(db: AsyncSession) -> List[PermissionModel]:
    result = await db.execute(
        select(PermissionModel).order_by(PermissionModel.code)
    )
    return result.scalars().all()


async def assign_permissions_to_role(
    db: AsyncSession,
    role_id: int,
    permission_codes: List[str],
    tenant_id: int
) -> None:
    for permission_code in permission_codes:
        permission = await db.execute(
            select(PermissionModel).where(PermissionModel.code == permission_code)
        )
        permission = permission.scalar_one_or_none()
        
        if not permission:
            continue
        
        existing = await db.execute(
            select(RolePermissionModel).where(
                RolePermissionModel.role_id == role_id,
                RolePermissionModel.permission_id == permission.id,
                RolePermissionModel.tenant_id == tenant_id
            )
        )
        existing_role_permission = existing.scalar_one_or_none()
        
        if not existing_role_permission:
            role_permission = RolePermissionModel(
                role_id=role_id,
                permission_id=permission.id,
                tenant_id=tenant_id
            )
            db.add(role_permission)
    
    await db.commit()


async def remove_permissions_from_role(
    db: AsyncSession,
    role_id: int,
    permission_codes: List[str],
    tenant_id: int
) -> None:
    for permission_code in permission_codes:
        permission = await db.execute(
            select(PermissionModel).where(PermissionModel.code == permission_code)
        )
        permission = permission.scalar_one_or_none()
        
        if not permission:
            continue
        
        await db.execute(
            select(RolePermissionModel).where(
                RolePermissionModel.role_id == role_id,
                RolePermissionModel.permission_id == permission.id,
                RolePermissionModel.tenant_id == tenant_id
            )
        )
        
        from sqlalchemy import delete as sql_delete
        await db.execute(
            sql_delete(RolePermissionModel).where(
                RolePermissionModel.role_id == role_id,
                RolePermissionModel.permission_id == permission.id,
                RolePermissionModel.tenant_id == tenant_id
            )
        )
    
    await db.commit()


async def get_permissions_for_role(
    db: AsyncSession,
    role_id: int,
    tenant_id: int
) -> List[str]:
    result = await db.execute(
        select(PermissionModel.code)
        .join(RolePermissionModel, PermissionModel.id == RolePermissionModel.permission_id)
        .where(
            RolePermissionModel.role_id == role_id,
            RolePermissionModel.tenant_id == tenant_id
        )
    )
    return [row[0] for row in result.all()]


async def assign_roles_to_user(
    db: AsyncSession,
    user_id: int,
    role_ids: List[int],
    tenant_id: int
) -> None:
    for role_id in role_ids:
        existing = await db.execute(
            select(UserRoleModel).where(
                UserRoleModel.user_id == user_id,
                UserRoleModel.role_id == role_id,
                UserRoleModel.tenant_id == tenant_id
            )
        )
        existing_user_role = existing.scalar_one_or_none()
        
        if not existing_user_role:
            user_role = UserRoleModel(
                user_id=user_id,
                role_id=role_id,
                tenant_id=tenant_id
            )
            db.add(user_role)
    
    await db.commit()


async def remove_roles_from_user(
    db: AsyncSession,
    user_id: int,
    role_ids: List[int],
    tenant_id: int
) -> None:
    for role_id in role_ids:
        from sqlalchemy import delete as sql_delete
        await db.execute(
            sql_delete(UserRoleModel).where(
                UserRoleModel.user_id == user_id,
                UserRoleModel.role_id == role_id,
                UserRoleModel.tenant_id == tenant_id
            )
        )
    
    await db.commit()


async def get_roles_for_user(
    db: AsyncSession,
    user_id: int,
    tenant_id: int
) -> List[int]:
    result = await db.execute(
        select(UserRoleModel.role_id).where(
            UserRoleModel.user_id == user_id,
            UserRoleModel.tenant_id == tenant_id
        )
    )
    return [row[0] for row in result.all()]


async def validate_permissions_consistency(db: AsyncSession) -> dict:
    """验证权限数据一致性"""
    from app.core.constants.permissions import PERMISSIONS_BY_MODULE
    
    result = {
        "valid": True,
        "issues": [],
        "summary": {}
    }
    
    expected_permissions = set()
    for module, permissions in PERMISSIONS_BY_MODULE.items():
        expected_permissions.update(permissions)
    
    db_permissions = await db.execute(select(PermissionModel))
    db_permissions = {p.code: p for p in db_permissions.scalars().all()}
    
    missing_in_db = expected_permissions - set(db_permissions.keys())
    extra_in_db = set(db_permissions.keys()) - expected_permissions
    
    if missing_in_db:
        result["valid"] = False
        result["issues"].append({
            "type": "missing_permissions",
            "message": f"代码中定义但数据库中缺失的权限: {len(missing_in_db)} 个",
            "details": list(missing_in_db)
        })
    
    if extra_in_db:
        result["issues"].append({
            "type": "extra_permissions",
            "message": f"数据库中存在但代码中未定义的权限: {len(extra_in_db)} 个",
            "details": list(extra_in_db)
        })
    
    result["summary"]["expected_permissions"] = len(expected_permissions)
    result["summary"]["db_permissions"] = len(db_permissions)
    result["summary"]["missing_in_db"] = len(missing_in_db)
    result["summary"]["extra_in_db"] = len(extra_in_db)
    
    return result


async def validate_user_roles_consistency(db: AsyncSession) -> dict:
    """验证用户角色关系一致性"""
    result = {
        "valid": True,
        "issues": [],
        "summary": {}
    }
    
    user_roles = await db.execute(select(UserRoleModel))
    user_roles = user_roles.scalars().all()
    
    user_ids = list({ur.user_id for ur in user_roles})
    role_ids = list({ur.role_id for ur in user_roles})
    
    users = await db.execute(select(UserModel).where(UserModel.id.in_(user_ids)))
    users = {u.id: u for u in users.scalars().all()}
    
    roles = await db.execute(select(RoleModel).where(RoleModel.id.in_(role_ids)))
    roles = {r.id: r for r in roles.scalars().all()}
    
    invalid_user_roles = []
    for ur in user_roles:
        if ur.user_id not in users:
            invalid_user_roles.append({
                "user_role_id": f"{ur.user_id}-{ur.role_id}",
                "reason": "用户不存在",
                "user_id": ur.user_id,
                "role_id": ur.role_id
            })
        elif ur.role_id not in roles:
            invalid_user_roles.append({
                "user_role_id": f"{ur.user_id}-{ur.role_id}",
                "reason": "角色不存在",
                "user_id": ur.user_id,
                "role_id": ur.role_id
            })
        elif ur.tenant_id != users[ur.user_id].tenant_id:
            invalid_user_roles.append({
                "user_role_id": f"{ur.user_id}-{ur.role_id}",
                "reason": "租户ID不一致",
                "user_id": ur.user_id,
                "role_id": ur.role_id,
                "user_tenant_id": users[ur.user_id].tenant_id,
                "user_role_tenant_id": ur.tenant_id
            })
    
    if invalid_user_roles:
        result["valid"] = False
        result["issues"].append({
            "type": "invalid_user_roles",
            "message": f"无效的用户角色关系: {len(invalid_user_roles)} 条",
            "details": invalid_user_roles
        })
    
    result["summary"]["total_user_roles"] = len(user_roles)
    result["summary"]["invalid_user_roles"] = len(invalid_user_roles)
    
    return result


async def validate_role_permissions_consistency(db: AsyncSession) -> dict:
    """验证角色权限关系一致性"""
    result = {
        "valid": True,
        "issues": [],
        "summary": {}
    }
    
    role_permissions = await db.execute(select(RolePermissionModel))
    role_permissions = role_permissions.scalars().all()
    
    role_ids = list({rp.role_id for rp in role_permissions})
    permission_ids = list({rp.permission_id for rp in role_permissions})
    
    roles = await db.execute(select(RoleModel).where(RoleModel.id.in_(role_ids)))
    roles = {r.id: r for r in roles.scalars().all()}
    
    permissions = await db.execute(select(PermissionModel).where(PermissionModel.id.in_(permission_ids)))
    permissions = {p.id: p for p in permissions.scalars().all()}
    
    invalid_role_permissions = []
    for rp in role_permissions:
        if rp.role_id not in roles:
            invalid_role_permissions.append({
                "role_permission_id": f"{rp.role_id}-{rp.permission_id}",
                "reason": "角色不存在",
                "role_id": rp.role_id,
                "permission_id": rp.permission_id
            })
        elif rp.permission_id not in permissions:
            invalid_role_permissions.append({
                "role_permission_id": f"{rp.role_id}-{rp.permission_id}",
                "reason": "权限不存在",
                "role_id": rp.role_id,
                "permission_id": rp.permission_id
            })
        elif rp.tenant_id != roles[rp.role_id].tenant_id:
            invalid_role_permissions.append({
                "role_permission_id": f"{rp.role_id}-{rp.permission_id}",
                "reason": "租户ID不一致",
                "role_id": rp.role_id,
                "permission_id": rp.permission_id,
                "role_tenant_id": roles[rp.role_id].tenant_id,
                "role_permission_tenant_id": rp.tenant_id
            })
    
    if invalid_role_permissions:
        result["valid"] = False
        result["issues"].append({
            "type": "invalid_role_permissions",
            "message": f"无效的角色权限关系: {len(invalid_role_permissions)} 条",
            "details": invalid_role_permissions
        })
    
    result["summary"]["total_role_permissions"] = len(role_permissions)
    result["summary"]["invalid_role_permissions"] = len(invalid_role_permissions)
    
    return result


async def validate_rbac_consistency(db: AsyncSession) -> dict:
    """验证RBAC整体一致性"""
    permissions_result = await validate_permissions_consistency(db)
    user_roles_result = await validate_user_roles_consistency(db)
    role_permissions_result = await validate_role_permissions_consistency(db)
    
    overall_valid = (
        permissions_result["valid"] and
        user_roles_result["valid"] and
        role_permissions_result["valid"]
    )
    
    return {
        "valid": overall_valid,
        "permissions": permissions_result,
        "user_roles": user_roles_result,
        "role_permissions": role_permissions_result,
        "total_issues": sum(len(r["issues"]) for r in [permissions_result, user_roles_result, role_permissions_result])
    }

