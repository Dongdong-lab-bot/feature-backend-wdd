from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.responses import Response
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.modules.device.schemas import (
    DeviceCreateRequest,
    DeviceRecordExportQuery,
    DeviceRecordQuery,
    DeviceRecordUpdateRequest,
    DeviceRefreshRequest,
    DeviceUpdateRequest,
    GenericResponse,
    MorningCheckUploadRequest,
)
from app.modules.device.service import (
    create_device,
    delete_device,
    export_device_records,
    get_device_tree,
    get_device_record_detail,
    get_device_detail,
    ingest_morning_check_message,
    list_device_records,
    refresh_device_heartbeat,
    update_device_record,
    update_device,
)
from app.modules.user.models import User

router = APIRouter()


def _raise_bad_request(msg: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"code": 40000, "msg": msg, "data": None},
    )


@router.get("/devices/records", response_model=GenericResponse)
async def get_device_record_list(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    page: int = Query(1),
    page_size: int = Query(20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        query = DeviceRecordQuery(
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size,
        )
    except ValidationError as exc:
        _raise_bad_request(str(exc))

    data = await list_device_records(
        db=db,
        tenant_id=current_user.tenant_id,
        query=query,
        current_user=current_user,
    )
    return GenericResponse(code=200, msg="success", data=data)


@router.get("/devices/tree", response_model=GenericResponse)
async def get_devices_tree(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tree = await get_device_tree(
        db=db,
        tenant_id=current_user.tenant_id,
        current_user=current_user,
    )
    return GenericResponse(code=200, msg="success", data=tree)


@router.get("/devices/records/export")
async def export_records(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    format_value: str = Query("excel", alias="format"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        query = DeviceRecordExportQuery(
            start_date=start_date,
            end_date=end_date,
            format=format_value,
        )
    except ValidationError as exc:
        _raise_bad_request(str(exc))

    export_result = await export_device_records(
        db=db,
        tenant_id=current_user.tenant_id,
        query=query,
        current_user=current_user,
    )
    return Response(
        content=export_result["content"],
        media_type=export_result["media_type"],
        headers={"Content-Disposition": f'attachment; filename="{export_result["filename"]}"'},
    )


@router.get("/devices/records/{id}", response_model=GenericResponse)
async def get_device_record(
    record_id: int = Path(..., ge=1, alias="id"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = await get_device_record_detail(
        db=db,
        tenant_id=current_user.tenant_id,
        record_id=record_id,
        current_user=current_user,
    )
    return GenericResponse(code=200, msg="success", data=data)


@router.put("/devices/records/{id}", response_model=GenericResponse)
async def put_device_record(
    request: DeviceRecordUpdateRequest,
    record_id: int = Path(..., ge=1, alias="id"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payload = request.model_dump(exclude_unset=True)
    if "status" in payload and payload["status"] is not None:
        payload["status"] = payload["status"].value
    if "data_type" in payload and payload["data_type"] is not None:
        payload["data_type"] = payload["data_type"].value
    if not payload:
        _raise_bad_request("至少需要一个更新字段")

    data = await update_device_record(
        db=db,
        tenant_id=current_user.tenant_id,
        record_id=record_id,
        payload=payload,
        current_user=current_user,
    )
    return GenericResponse(code=200, msg="success", data=data)


@router.post("/devices/upload/morning-check", response_model=GenericResponse)
async def post_morning_check_upload(
    request: MorningCheckUploadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = await ingest_morning_check_message(
        db=db,
        tenant_id=current_user.tenant_id,
        payload=request.model_dump(),
    )
    return GenericResponse(code=200, msg="success", data=data)


@router.post("/devices/refresh", response_model=GenericResponse)
async def post_device_refresh(
    request: DeviceRefreshRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = await refresh_device_heartbeat(
        db=db,
        tenant_id=current_user.tenant_id,
        device_code=request.device_code,
    )
    return GenericResponse(code=200, msg="success", data=data)


@router.get("/devices/{id}", response_model=GenericResponse)
async def get_device(
    device_id: int = Path(..., ge=1, alias="id"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = await get_device_detail(
        db=db,
        tenant_id=current_user.tenant_id,
        device_id=device_id,
        current_user=current_user,
    )
    return GenericResponse(code=200, msg="success", data=data)


@router.post("/devices", response_model=GenericResponse)
async def post_device(
    request: DeviceCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    device = await create_device(
        db=db,
        tenant_id=current_user.tenant_id,
        payload=request.model_dump(),
    )
    return GenericResponse(code=200, msg="success", data={"id": device.id})


@router.put("/devices/{id}", response_model=GenericResponse)
async def put_device(
    request: DeviceUpdateRequest,
    device_id: int = Path(..., ge=1, alias="id"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payload = request.model_dump(exclude_unset=True)
    if not payload:
        _raise_bad_request("至少需要一个更新字段")

    device = await update_device(
        db=db,
        tenant_id=current_user.tenant_id,
        device_id=device_id,
        payload=payload,
        current_user=current_user,
    )
    return GenericResponse(code=200, msg="success", data={"id": device.id})


@router.delete("/devices/{id}", response_model=GenericResponse)
async def remove_device(
    device_id: int = Path(..., ge=1, alias="id"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    deleted = await delete_device(
        db=db,
        tenant_id=current_user.tenant_id,
        device_id=device_id,
        current_user=current_user,
    )
    return GenericResponse(code=200, msg="success", data={"id": device_id, "deleted": deleted})
