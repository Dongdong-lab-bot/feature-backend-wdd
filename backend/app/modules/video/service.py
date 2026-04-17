from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache
from app.core.config import settings
from app.core.context import system_mode_scope
from app.modules.video.models import BizVideoCamera


class HikvisionAuthService:
    _CACHE_KEY = "hikvision:oauth:access_token"
    _LEEWAY_SECONDS = 60

    @classmethod
    async def get_access_token(cls, force_refresh: bool = False) -> str:
        if not settings.hikvision_client_id or not settings.hikvision_client_secret:
            raise HTTPException(
                status_code=500,
                detail={"code": 500, "msg": "hikvision client config missing", "data": None},
            )

        if not force_refresh:
            cached = cls._get_cached_token()
            if cached:
                return cached

        token_data = await cls._request_access_token()
        cls._cache_token(token_data)
        return token_data["access_token"]

    @classmethod
    def _get_cached_token(cls) -> Optional[str]:
        with system_mode_scope():
            cached = cache.get(cls._CACHE_KEY)
        if not cached:
            return None
        access_token = cached.get("access_token")
        expires_at = cached.get("expires_at")
        if not access_token or not expires_at:
            return None
        now = int(time.time())
        if int(expires_at) <= now + cls._LEEWAY_SECONDS:
            return None
        return str(access_token)

    @classmethod
    async def _request_access_token(cls) -> dict:
        payload = {
            "client_id": settings.hikvision_client_id,
            "client_secret": settings.hikvision_client_secret,
            "grant_type": "client_credentials",
            "scope": settings.hikvision_oauth_scope,
        }
        timeout = settings.hikvision_oauth_timeout_seconds
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(settings.hikvision_oauth_url, json=payload)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=502,
                detail={"code": 502, "msg": f"hikvision oauth failed: {exc}", "data": None},
            ) from exc

        data = response.json()
        access_token = data.get("access_token")
        expires_in = data.get("expires_in")
        if not access_token or not expires_in:
            raise HTTPException(
                status_code=502,
                detail={"code": 502, "msg": "hikvision oauth invalid response", "data": None},
            )

        now = int(time.time())
        return {
            "access_token": access_token,
            "expires_at": now + int(expires_in),
            "expires_in": int(expires_in),
        }

    @classmethod
    def _cache_token(cls, token_data: dict) -> None:
        expires_in = int(token_data.get("expires_in", 0))
        ttl = max(60, expires_in - cls._LEEWAY_SECONDS)
        payload = {
            "access_token": token_data["access_token"],
            "expires_at": token_data["expires_at"],
        }
        with system_mode_scope():
            cache.set(cls._CACHE_KEY, payload, expire=ttl)


class HikvisionOpenApiService:
    _BASE_URL = "https://api2.hik-cloud.com"
    _SYNC_PATH = "/api/v1/open/basic/channels/actions/sync"
    _SYNC_NAME_PATH = "/api/v1/open/basic/channels/actions/name/sync"
    _LIST_PATH = "/api/v1/open/basic/channels/list"
    _ENCRYPT_OFF_PATH = "/api/v1/open/basic/devices/actions/encrypt/off"
    _EZVIZ_ACCOUNT_INFO_PATH = "/v1/ezviz/account/info"

    @classmethod
    async def sync_channels(
        cls,
        db: AsyncSession,
        tenant_id: int,
        device_serial: str,
        page_size: int = 50,
    ) -> dict:
        access_token = await HikvisionAuthService.get_access_token()
        await cls._request(
            "POST",
            cls._SYNC_PATH,
            access_token,
            json_body={"deviceSerial": device_serial},
        )
        await cls._request(
            "POST",
            cls._SYNC_NAME_PATH,
            access_token,
            json_body={"deviceSerial": device_serial},
        )
        channels = await cls._list_channels(access_token, device_serial, page_size)
        created, updated = await cls._upsert_channels(db, tenant_id, device_serial, channels)
        return {
            "deviceSerial": device_serial,
            "synced": True,
            "nameSynced": True,
            "total": len(channels),
            "created": created,
            "updated": updated,
        }

    @classmethod
    async def disable_encrypt(
        cls,
        db: AsyncSession,
        tenant_id: int,
        device_serial: str,
        validate_code: Optional[str] = None,
    ) -> dict:
        access_token = await HikvisionAuthService.get_access_token()
        payload = {"deviceSerial": device_serial}
        if validate_code:
            payload["validateCode"] = validate_code
        await cls._request("POST", cls._ENCRYPT_OFF_PATH, access_token, json_body=payload)
        stmt = select(BizVideoCamera).where(
            BizVideoCamera.tenant_id == tenant_id,
            BizVideoCamera.device_serial == device_serial,
        )
        cameras = (await db.execute(stmt)).scalars().all()
        if not cameras:
            raise HTTPException(
                status_code=404,
                detail={"code": 40400, "msg": "camera not found", "data": None},
            )
        now = datetime.now(timezone.utc)
        for camera in cameras:
            camera.encrypt_enabled = False
            if validate_code:
                camera.valid_code = validate_code
            camera.updated_at = now
        await db.commit()
        return {
            "deviceSerial": device_serial,
            "encryptEnabled": False,
            "updated": len(cameras),
        }

    @classmethod
    async def get_stream_auth_info(cls) -> dict:
        access_token = await HikvisionAuthService.get_access_token()
        data = await cls._request("GET", cls._EZVIZ_ACCOUNT_INFO_PATH, access_token)
        payload = data.get("data") or {}
        app_key = payload.get("appKey") or payload.get("app_key")
        token = payload.get("token")
        if not app_key or not token:
            raise HTTPException(
                status_code=502,
                detail={"code": 502, "msg": "hikvision stream auth invalid response", "data": data},
            )
        return {"appKey": str(app_key), "token": str(token)}

    @classmethod
    async def _list_channels(
        cls,
        access_token: str,
        device_serial: str,
        page_size: int,
    ) -> list:
        results: list = []
        page_no = 1
        while True:
            data = await cls._request(
                "GET",
                cls._LIST_PATH,
                access_token,
                params={
                    "deviceSerial": device_serial,
                    "pageNo": page_no,
                    "pageSize": page_size,
                },
            )
            container = data.get("data") if isinstance(data.get("data"), dict) else data
            rows = container.get("rows") or container.get("list") or []
            results.extend(rows)
            total = container.get("total")
            if not rows:
                break
            if total is None:
                if len(rows) < page_size:
                    break
            else:
                try:
                    total_int = int(total)
                except (TypeError, ValueError):
                    total_int = len(results)
                if page_no * page_size >= total_int:
                    break
            page_no += 1
        return results

    @classmethod
    async def _upsert_channels(
        cls,
        db: AsyncSession,
        tenant_id: int,
        device_serial: str,
        channels: list,
    ) -> tuple[int, int]:
        created = 0
        updated = 0
        now = datetime.now(timezone.utc)
        for channel in channels:
            channel_no = channel.get("channelNo") or channel.get("channel_no")
            if channel_no is None:
                continue
            channel_no = str(channel_no)
            stmt = select(BizVideoCamera).where(
                BizVideoCamera.tenant_id == tenant_id,
                BizVideoCamera.device_serial == device_serial,
                BizVideoCamera.channel_no == channel_no,
            )
            camera = (await db.execute(stmt)).scalar_one_or_none()
            if camera:
                updated += 1
            else:
                channel_id = channel.get("channelId")
                camera_id = str(channel_id) if channel_id else f"{device_serial}:{channel_no}"
                camera = BizVideoCamera(
                    tenant_id=tenant_id,
                    camera_id=camera_id,
                    device_serial=device_serial,
                    channel_no=channel_no,
                )
                db.add(camera)
                created += 1
            channel_name = channel.get("channelName")
            if channel_name is not None:
                camera.channel_name = str(channel_name)
            channel_type = channel.get("channelType")
            if channel_type is not None:
                camera.channel_type = str(channel_type)
            channel_status = channel.get("channelStatus")
            if channel_status is not None:
                camera.channel_status = str(channel_status)
            is_use = channel.get("isUse")
            if is_use is not None:
                camera.is_use = cls._normalize_bool(is_use)
            ipc_serial = channel.get("ipcSerial")
            if ipc_serial is not None:
                camera.ipc_serial = str(ipc_serial)
            camera.last_synced_at = now
        await db.commit()
        return created, updated

    @classmethod
    def _normalize_bool(cls, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        if isinstance(value, (int, float)):
            return bool(value)
        text = str(value).strip().lower()
        if text in {"1", "true", "yes", "y", "on"}:
            return True
        return False

    @classmethod
    async def _request(
        cls,
        method: str,
        path: str,
        access_token: str,
        params: Optional[dict] = None,
        json_body: Optional[dict] = None,
    ) -> dict:
        headers = {"Authorization": f"Bearer {access_token}"}
        timeout = settings.hikvision_oauth_timeout_seconds
        url = f"{cls._BASE_URL}{path}"
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(
                    method,
                    url,
                    headers=headers,
                    params=params,
                    json=json_body,
                )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=502,
                detail={"code": 502, "msg": f"hikvision api failed: {exc}", "data": None},
            ) from exc
        data = response.json()
        code = data.get("code")
        if code not in (None, 200, "200"):
            msg = data.get("message") or data.get("msg") or "hikvision api error"
            raise HTTPException(
                status_code=502,
                detail={"code": 502, "msg": msg, "data": data},
            )
        return data


__all__ = ["HikvisionAuthService", "HikvisionOpenApiService"]