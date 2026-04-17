from __future__ import annotations

from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.device.models import BizDevice


def _raise_http_error(http_status: int, code: int, msg: str) -> None:
    raise HTTPException(status_code=http_status, detail={"code": code, "msg": msg, "data": None})


async def authenticate_device_by_api_key(
    db: AsyncSession = Depends(get_db),
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
) -> BizDevice:
    api_key = (x_api_key or "").strip()
    if not api_key:
        _raise_http_error(status.HTTP_401_UNAUTHORIZED, 40101, "无效的API Key")

    try:
        device = (
            await db.execute(
                select(BizDevice).where(
                    BizDevice.api_key == api_key,
                    BizDevice.is_deleted.is_(False),
                )
            )
        ).scalar_one_or_none()
    except SQLAlchemyError:
        _raise_http_error(status.HTTP_500_INTERNAL_SERVER_ERROR, 50010, "设备鉴权失败")

    if device is None:
        _raise_http_error(status.HTTP_401_UNAUTHORIZED, 40101, "无效的API Key")
    if device.status == "MAINTENANCE":
        _raise_http_error(status.HTTP_403_FORBIDDEN, 40302, "设备维护中")
    return device
