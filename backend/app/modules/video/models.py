from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base
from app.db.mixins import TenantMixin


class BizVideoCamera(Base, TenantMixin):
    __tablename__ = "biz_video_camera"
    __table_args__ = (
        UniqueConstraint("tenant_id", "camera_id", name="uq_video_camera_tenant_camera"),
        UniqueConstraint(
            "tenant_id",
            "device_serial",
            "channel_no",
            name="uq_video_camera_tenant_device_channel",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    camera_id: Mapped[str] = mapped_column(String(64), nullable=False, comment="业务摄像头/点位ID")
    device_serial: Mapped[str] = mapped_column(String(64), nullable=False, comment="海康设备序列号")
    channel_no: Mapped[str] = mapped_column(String(32), nullable=False, comment="海康通道号")
    canteen_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("orgs.id"), nullable=True, index=True, comment="所属食堂ID"
    )

    encrypt_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="设备视频是否加密"
    )
    valid_code: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="设备验证码"
    )

    channel_name: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, comment="通道名称"
    )
    channel_type: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True, comment="通道类型"
    )
    channel_status: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True, comment="通道状态"
    )
    is_use: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True, comment="通道是否可用"
    )
    ipc_serial: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="IPC 序列号"
    )

    last_synced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="最近一次通道同步时间"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="业务侧是否启用"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now()
    )


__all__ = ["BizVideoCamera"]
