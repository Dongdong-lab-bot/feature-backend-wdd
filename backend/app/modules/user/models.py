from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TenantMixin


def _utcnow() -> datetime:
    """Return a timezone-aware UTC datetime for default columns."""
    return datetime.now(timezone.utc)


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    __table_args__ = (
        CheckConstraint("status in ('ACTIVE','DISABLED')", name="ck_tenant_status"),
    )


class Org(Base, TenantMixin):
    __tablename__ = "orgs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("orgs.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    org_type: Mapped[str] = mapped_column(String(16), nullable=False)
    manager_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", name="fk_org_manager_user", use_alter=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "parent_id", "name", name="uq_org_name_parent"),
        CheckConstraint("org_type in ('AREA','SCHOOL','CANTEEN')", name="ck_org_type"),
        Index("ix_org_tenant", "tenant_id"),
        Index("ix_org_parent", "parent_id"),
    )


class User(Base, TenantMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    org_id: Mapped[Optional[int]] = mapped_column(ForeignKey("orgs.id"), nullable=True)
    role_id: Mapped[Optional[int]] = mapped_column(ForeignKey("roles.id"), nullable=True)
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    real_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    mobile: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    birthday: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    canteen_scope: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    face_image_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    health_image_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role_type: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE")
    token_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "username", name="uq_user_tenant_username"),
        CheckConstraint("role_type in ('REGULATOR','EXECUTOR')", name="ck_user_role_type"),
        CheckConstraint("status in ('ACTIVE','DISABLED')", name="ck_user_status"),
        Index("ix_user_tenant", "tenant_id"),
        Index("ix_user_org", "org_id"),
        Index("ix_user_mobile", "mobile"),
        Index("ix_user_tenant_mobile", "tenant_id", "mobile"),
    )


class Role(Base, TenantMixin):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    role_type: Mapped[str] = mapped_column(String(16), nullable=False)
    level: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    permissions_desc: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_role_tenant_name"),
        CheckConstraint("role_type in ('REGULATOR','EXECUTOR')", name="ck_role_type"),
        Index("ix_role_tenant", "tenant_id"),
    )


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)

    __table_args__ = (
        UniqueConstraint("code", name="uq_permission_code"),
    )


class UserRole(Base, TenantMixin):
    __tablename__ = "user_roles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)

    __table_args__ = (
        Index("ix_user_role_tenant", "tenant_id"),
    )


class RolePermission(Base, TenantMixin):
    __tablename__ = "role_permissions"

    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), primary_key=True)
    permission_id: Mapped[int] = mapped_column(ForeignKey("permissions.id"), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)

    __table_args__ = (
        Index("ix_role_permission_tenant", "tenant_id"),
    )


class ExternalIdentity(Base):
    __tablename__ = "external_identities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    issuer: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    raw_claims: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)

    __table_args__ = (
        UniqueConstraint("issuer", "subject", name="uq_external_issuer_subject"),
        Index("ix_external_user", "user_id"),
    )


class Menu(Base):
    __tablename__ = "menus"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("menus.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    path: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    component: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    hidden: Mapped[bool] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    __table_args__ = (
        Index("ix_menu_parent", "parent_id"),
    )


class RefreshToken(Base, TenantMixin):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    app_client: Mapped[str] = mapped_column(String(32), nullable=False)
    jti: Mapped[str] = mapped_column(String(64), nullable=False)
    family_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("jti", name="uq_refresh_token_jti"),
        Index("ix_refresh_token_user", "user_id"),
        Index("ix_refresh_token_tenant", "tenant_id"),
        Index("ix_refresh_token_app_client", "app_client"),
        Index("ix_refresh_token_valid_lookup", "user_id", "revoked_at", "expires_at"),
    )


class Image(Base):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    filepath: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)

    __table_args__ = (
        Index("ix_image_tenant", "tenant_id"),
        Index("ix_image_user", "user_id"),
    )
