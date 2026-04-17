from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TenantMixin
from app.modules.ledger.models import DeviceBuffer as BizDeviceBuffer


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BizDevice(Base, TenantMixin):
    __tablename__ = "biz_device"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("orgs.id"), nullable=False)
    device_name: Mapped[str] = mapped_column(String(128), nullable=False)
    device_code: Mapped[str] = mapped_column(String(64), nullable=False)
    device_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    api_key: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="设备API Key")
    vendor: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    installed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="OFFLINE")
    last_heartbeat: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    extra: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    records: Mapped[list["BizDeviceRecord"]] = relationship(back_populates="device")

    __table_args__ = (
        UniqueConstraint("tenant_id", "device_code", name="uq_biz_device_tenant_code"),
        UniqueConstraint("api_key", name="uq_biz_device_api_key"),
        Index("ix_biz_device_tenant_org", "tenant_id", "org_id"),
        Index("ix_biz_device_tenant_status", "tenant_id", "status"),
        Index("ix_biz_device_tenant_deleted", "tenant_id", "is_deleted"),
    )


class BizDeviceRecord(Base, TenantMixin):
    __tablename__ = "biz_device_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("biz_device.id"), nullable=False)
    org_id: Mapped[int] = mapped_column(ForeignKey("orgs.id"), nullable=False)
    data_type: Mapped[str] = mapped_column(String(64), nullable=False)
    is_related_ledger: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    submit_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    detail_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="DEVICE_AUTO")
    trace_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    process_result: Mapped[str] = mapped_column(String(32), nullable=False, default="SUCCESS")
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    device: Mapped[BizDevice] = relationship(back_populates="records")

    __table_args__ = (
        Index("ix_device_record_tenant_submit", "tenant_id", "submit_date"),
        Index("ix_device_record_tenant_org_submit", "tenant_id", "org_id", "submit_date"),
        Index("ix_device_record_tenant_type_submit", "tenant_id", "data_type", "submit_date"),
        Index("ix_device_record_tenant_device_submit", "tenant_id", "device_id", "submit_date"),
        Index("ix_device_record_tenant_deleted", "tenant_id", "is_deleted"),
    )


__all__ = ["BizDevice", "BizDeviceRecord", "BizDeviceBuffer"]
