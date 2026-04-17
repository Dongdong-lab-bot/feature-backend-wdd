from __future__ import annotations

import csv
from io import BytesIO, StringIO
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Set
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from app.modules.device.constants import (
    AI_BOX_EVENT_TYPES,
    DATA_TYPE_AI_BOX_CODE,
    DATA_TYPE_AI_BOX_LABEL,
    DATA_TYPE_MORNING_CHECK_CODE,
    DATA_TYPE_MORNING_CHECK_LABEL,
    DATA_TYPE_SAMPLING_CODE,
    DATA_TYPE_SAMPLING_LABEL,
    PROCESS_RESULT_FAILED,
    PROCESS_RESULT_PARTIAL_SUCCESS,
    PROCESS_RESULT_SUCCESS,
    SOURCE_DEVICE_AUTO,
    get_temperature_status,
)
from app.modules.device.integrations.alert_service import build_alert_types, dispatch_device_alerts
from app.modules.device.integrations.ledger_backfill import backfill_morning_check_ledger
from app.modules.device.models import BizDevice, BizDeviceRecord
from app.modules.device.schemas import (
    AIBoxRecordData,
    DeviceRecordExportQuery,
    DeviceRecordQuery,
    DeviceRecordType,
    GenericRecordData,
    MorningCheckRecordData,
    SamplingRecordData,
)
from app.modules.user.models import Org as OrgModel, User

DATA_TYPE_LABELS = {
    DATA_TYPE_MORNING_CHECK_CODE: DATA_TYPE_MORNING_CHECK_LABEL,
    DATA_TYPE_AI_BOX_CODE: DATA_TYPE_AI_BOX_LABEL,
    DATA_TYPE_SAMPLING_CODE: DATA_TYPE_SAMPLING_LABEL,
}


def _safe_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _get_record_type(data_type: str) -> DeviceRecordType:
    type_mapping = {
        DATA_TYPE_MORNING_CHECK_CODE: DeviceRecordType.MORNING_CHECK,
        DATA_TYPE_AI_BOX_CODE: DeviceRecordType.AI_BOX,
        DATA_TYPE_SAMPLING_CODE: DeviceRecordType.SAMPLING,
    }
    return type_mapping.get(data_type, DeviceRecordType.GENERIC)


def _build_morning_check_record_data(detail_json: Dict[str, Any], payload: Dict[str, Any]) -> MorningCheckRecordData:
    device_info = _safe_dict(detail_json.get("device_info"))
    employee_info = _safe_dict(detail_json.get("employee_info"))
    inspection_data = _safe_dict(detail_json.get("inspection_data"))

    temperature = inspection_data.get("temperature", payload.get("temperature", 0.0))
    if not isinstance(temperature, (int, float)):
        temperature = 0.0

    return MorningCheckRecordData(
        employee_id=str(employee_info.get("employee_id") or payload.get("employee_id") or ""),
        employee_name=str(employee_info.get("employee_name") or ""),
        temperature=float(temperature),
        temperature_status=get_temperature_status(float(temperature)),
        has_mask=bool(inspection_data.get("has_mask", payload.get("has_mask", False))),
        has_wound=bool(inspection_data.get("has_wound", payload.get("has_wound", False))),
        capture_image_url=inspection_data.get("capture_image_url"),
        occurred_at=str(device_info.get("timestamp") or ""),
    )


def _build_ai_box_record_data(detail_json: Dict[str, Any], payload: Dict[str, Any]) -> AIBoxRecordData:
    detail_info = _safe_dict(payload.get("info"))
    merged = {**detail_info, **detail_json}
    event_type = str(merged.get("event_type") or "")
    confidence = merged.get("confidence")
    if confidence is not None and not isinstance(confidence, (int, float)):
        confidence = None

    return AIBoxRecordData(
        event_type=event_type,
        event_type_label=AI_BOX_EVENT_TYPES.get(event_type, event_type),
        region_name=merged.get("region_name"),
        detect_result=merged.get("detect_result"),
        confidence=float(confidence) if isinstance(confidence, (int, float)) else None,
        snapshot_url=merged.get("snapshot_url"),
        occurred_at=str(merged.get("time") or ""),
    )


def _build_sampling_record_data(detail_json: Dict[str, Any], payload: Dict[str, Any]) -> SamplingRecordData:
    merged = {**payload, **detail_json}
    weight = merged.get("weight", 0.0)
    if not isinstance(weight, (int, float)):
        weight = 0.0
    return SamplingRecordData(
        dish_name=str(merged.get("dish_name") or ""),
        stall_name=merged.get("stall_name"),
        operator_name=merged.get("operator_name"),
        weight=float(weight),
        weight_unit=str(merged.get("unit") or "g"),
        occurred_at=str(merged.get("timestamp") or ""),
    )


def _build_generic_record_data(payload: Dict[str, Any], detail_json: Dict[str, Any]) -> GenericRecordData:
    return GenericRecordData(raw_payload=payload or None, raw_detail=detail_json or None)


def _build_record_data(data_type: str, payload: Dict[str, Any], detail_json: Dict[str, Any]) -> Any:
    record_type = _get_record_type(data_type)
    if record_type == DeviceRecordType.MORNING_CHECK:
        return _build_morning_check_record_data(detail_json, payload)
    if record_type == DeviceRecordType.AI_BOX:
        return _build_ai_box_record_data(detail_json, payload)
    if record_type == DeviceRecordType.SAMPLING:
        return _build_sampling_record_data(detail_json, payload)
    return _build_generic_record_data(payload, detail_json)


def _raise_http_error(http_status: int, code: int, msg: str) -> None:
    raise HTTPException(status_code=http_status, detail={"code": code, "msg": msg, "data": None})


def _normalize_device_code(device_code: str) -> str:
    code = device_code.strip()
    if not code:
        _raise_http_error(status.HTTP_400_BAD_REQUEST, 40000, "设备编码不能为空")
    return code.upper()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _to_device_data(device: BizDevice, org_name: Optional[str]) -> Dict[str, Any]:
    return {
        "id": device.id,
        "device_name": device.device_name,
        "device_code": device.device_code,
        "status": device.status,
        "created_at": device.created_at,
        "org_id": device.org_id,
        "org_name": org_name,
        "device_type": device.device_type,
    }


async def _visible_org_ids(db: AsyncSession, current_user: User) -> Set[int]:
    if current_user.role_type == "EXECUTOR":
        if current_user.org_id is None:
            return set()

        orgs = (
            await db.execute(
                select(OrgModel.id, OrgModel.parent_id, OrgModel.org_type).where(
                    OrgModel.tenant_id == current_user.tenant_id,
                )
            )
        ).all()
        if not orgs:
            return set()

        org_type_by_id = {org_id: org_type for org_id, _, org_type in orgs}
        if current_user.org_id not in org_type_by_id:
            return set()
        if org_type_by_id[current_user.org_id] == "CANTEEN":
            return {current_user.org_id}

        children_map: Dict[Optional[int], list[int]] = {}
        for org_id, parent_id, _ in orgs:
            children_map.setdefault(parent_id, []).append(org_id)

        visible_canteens: Set[int] = set()
        queue = [current_user.org_id]
        while queue:
            current = queue.pop(0)
            if org_type_by_id.get(current) == "CANTEEN":
                visible_canteens.add(current)
            queue.extend(children_map.get(current, []))
        return visible_canteens

    rows = (
        await db.execute(
            select(OrgModel.id).where(
                OrgModel.tenant_id == current_user.tenant_id,
                OrgModel.org_type == "CANTEEN",
            )
        )
    ).scalars().all()
    return set(rows)


async def _validate_canteen_org(db: AsyncSession, tenant_id: int, org_id: int) -> OrgModel:
    org = (
        await db.execute(
            select(OrgModel).where(
                OrgModel.tenant_id == tenant_id,
                OrgModel.id == org_id,
                OrgModel.org_type == "CANTEEN",
            )
        )
    ).scalar_one_or_none()
    if org is None:
        _raise_http_error(status.HTTP_400_BAD_REQUEST, 40004, "org_id不存在或不是食堂组织")
    return org


async def _find_device_by_code(
    db: AsyncSession,
    tenant_id: int,
    device_code: str,
    visible_org_ids: Optional[Set[int]] = None,
) -> Optional[BizDevice]:
    filters = [
        BizDevice.tenant_id == tenant_id,
        BizDevice.device_code == device_code,
        BizDevice.is_deleted.is_(False),
    ]
    if visible_org_ids is not None:
        filters.append(BizDevice.org_id.in_(visible_org_ids))
    return (await db.execute(select(BizDevice).where(*filters))).scalar_one_or_none()


async def create_device(db: AsyncSession, tenant_id: int, payload: Dict[str, Any]) -> BizDevice:
    try:
        await _validate_canteen_org(db, tenant_id, payload["org_id"])
        payload["device_code"] = _normalize_device_code(payload["device_code"])

        existing = (
            await db.execute(
                select(BizDevice).where(
                    BizDevice.tenant_id == tenant_id,
                    BizDevice.device_code == payload["device_code"],
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            _raise_http_error(status.HTTP_409_CONFLICT, 40901, "设备编码已存在")

        device = BizDevice(
            tenant_id=tenant_id,
            org_id=payload["org_id"],
            device_name=payload["device_name"],
            device_code=payload["device_code"],
            api_key=await _generate_unique_device_api_key(db),
            status=payload.get("status", "OFFLINE"),
            device_type=payload.get("device_type"),
            is_deleted=False,
        )
        db.add(device)
        await db.commit()
        await db.refresh(device)
        return device
    except HTTPException:
        await db.rollback()
        raise
    except SQLAlchemyError:
        await db.rollback()
        _raise_http_error(status.HTTP_500_INTERNAL_SERVER_ERROR, 50001, "创建设备失败")


async def get_device_detail(
    db: AsyncSession,
    tenant_id: int,
    device_id: int,
    current_user: User,
) -> Dict[str, Any]:
    visible_org_ids = await _visible_org_ids(db, current_user)
    if not visible_org_ids:
        _raise_http_error(status.HTTP_404_NOT_FOUND, 40401, "设备不存在")

    stmt = (
        select(BizDevice, OrgModel.name.label("org_name"))
        .join(OrgModel, BizDevice.org_id == OrgModel.id)
        .where(
            BizDevice.id == device_id,
            BizDevice.tenant_id == tenant_id,
            BizDevice.is_deleted.is_(False),
            BizDevice.org_id.in_(visible_org_ids),
        )
    )
    row = (await db.execute(stmt)).one_or_none()
    if row is None:
        _raise_http_error(status.HTTP_404_NOT_FOUND, 40401, "设备不存在")
    device, org_name = row
    return _to_device_data(device, org_name)


async def update_device(
    db: AsyncSession,
    tenant_id: int,
    device_id: int,
    payload: Dict[str, Any],
    current_user: User,
) -> BizDevice:
    try:
        visible_org_ids = await _visible_org_ids(db, current_user)
        if not visible_org_ids:
            _raise_http_error(status.HTTP_404_NOT_FOUND, 40401, "设备不存在")

        device = (
            await db.execute(
                select(BizDevice).where(
                    BizDevice.id == device_id,
                    BizDevice.tenant_id == tenant_id,
                    BizDevice.is_deleted.is_(False),
                    BizDevice.org_id.in_(visible_org_ids),
                )
            )
        ).scalar_one_or_none()
        if device is None:
            _raise_http_error(status.HTTP_404_NOT_FOUND, 40401, "设备不存在")

        allowed_fields = {"device_name", "status", "device_type"}
        for key in list(payload.keys()):
            if key not in allowed_fields:
                payload.pop(key, None)

        for key, value in payload.items():
            setattr(device, key, value)

        await db.commit()
        await db.refresh(device)
        return device
    except HTTPException:
        await db.rollback()
        raise
    except SQLAlchemyError:
        await db.rollback()
        _raise_http_error(status.HTTP_500_INTERNAL_SERVER_ERROR, 50002, "更新设备失败")


async def delete_device(
    db: AsyncSession,
    tenant_id: int,
    device_id: int,
    current_user: User,
) -> bool:
    try:
        visible_org_ids = await _visible_org_ids(db, current_user)
        if not visible_org_ids:
            return False

        device = (
            await db.execute(
                select(BizDevice).where(
                    BizDevice.id == device_id,
                    BizDevice.tenant_id == tenant_id,
                    BizDevice.org_id.in_(visible_org_ids),
                )
            )
        ).scalar_one_or_none()
        if device is None:
            return False

        if device.is_deleted:
            return False

        device.is_deleted = True
        await db.commit()
        return True
    except HTTPException:
        await db.rollback()
        raise
    except SQLAlchemyError:
        await db.rollback()
        _raise_http_error(status.HTTP_500_INTERNAL_SERVER_ERROR, 50003, "删除设备失败")


async def refresh_device_heartbeat(
    db: AsyncSession,
    tenant_id: int,
    device_code: str,
) -> Dict[str, Any]:
    normalized_code = _normalize_device_code(device_code)
    try:
        device = await _find_device_by_code(db, tenant_id, normalized_code)
        if device is None:
            _raise_http_error(status.HTTP_404_NOT_FOUND, 40401, "设备不存在")

        device.status = "ONLINE"
        device.last_heartbeat = _now()
        await db.commit()
        await db.refresh(device)
        return {"id": device.id, "device_code": device.device_code, "last_heartbeat": device.last_heartbeat}
    except HTTPException:
        await db.rollback()
        raise
    except SQLAlchemyError:
        await db.rollback()
        _raise_http_error(status.HTTP_500_INTERNAL_SERVER_ERROR, 50005, "设备保活失败")


async def ingest_morning_check_message(
    db: AsyncSession,
    tenant_id: int,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    device_info = payload["device_info"]
    employee_info = payload["employee_info"]
    inspection_data = payload["inspection_data"]
    normalized_code = _normalize_device_code(device_info["device_code"])
    trace_id = str(uuid4())

    try:
        device = await _find_device_by_code(db, tenant_id, normalized_code)
        if device is None:
            _raise_http_error(status.HTTP_404_NOT_FOUND, 40401, "设备不存在")

        device.status = "ONLINE"
        device.last_heartbeat = _now()

        ledger_payload = {
            "tenant_id": tenant_id,
            "device_id": device.id,
            "org_id": device.org_id,
            "device_code": device.device_code,
            "employee_id": employee_info["employee_id"],
            "employee_name": employee_info["employee_name"],
            "temperature": inspection_data["temperature"],
            "has_mask": inspection_data["has_mask"],
            "has_wound": inspection_data["has_wound"],
            "capture_image_url": inspection_data.get("capture_image_url"),
            "occurred_at": device_info["timestamp"],
            "trace_id": trace_id,
        }
        ledger_result = await backfill_morning_check_ledger(ledger_payload)
        ledger_success = bool(ledger_result.get("success", False))

        alert_types = build_alert_types(
            temperature=inspection_data["temperature"],
            has_mask=inspection_data["has_mask"],
        )
        alerts_success = True
        alert_error: Optional[str] = None
        if alert_types:
            alert_result = await dispatch_device_alerts(
                alert_types=alert_types,
                payload={"tenant_id": tenant_id, "device_id": device.id, "trace_id": trace_id},
            )
            alerts_success = bool(alert_result.get("success", False))
            alert_error = alert_result.get("error")

        process_result = PROCESS_RESULT_SUCCESS
        if not ledger_success:
            process_result = PROCESS_RESULT_FAILED
        elif not alerts_success:
            process_result = PROCESS_RESULT_PARTIAL_SUCCESS

        record = BizDeviceRecord(
            tenant_id=tenant_id,
            device_id=device.id,
            org_id=device.org_id,
            data_type=DATA_TYPE_MORNING_CHECK_CODE,
            is_related_ledger=ledger_success,
            submit_date=device_info["timestamp"].date(),
            status=device.status,
            payload={
                "temperature": inspection_data["temperature"],
                "has_mask": inspection_data["has_mask"],
                "has_wound": inspection_data["has_wound"],
                "employee_id": employee_info["employee_id"],
            },
            detail_json=payload,
            source=SOURCE_DEVICE_AUTO,
            trace_id=trace_id,
            process_result=process_result,
            is_deleted=False,
        )
        db.add(record)
        await db.commit()
        return {
            "trace_id": trace_id,
            "record_id": record.id,
            "process_result": process_result,
            "ledger_success": ledger_success,
            "alerts": alert_types,
            "alert_error": alert_error,
        }
    except HTTPException:
        await db.rollback()
        raise
    except SQLAlchemyError:
        await db.rollback()
        _raise_http_error(status.HTTP_500_INTERNAL_SERVER_ERROR, 50006, "晨检消息处理失败")
    except Exception:
        await db.rollback()
        _raise_http_error(status.HTTP_500_INTERNAL_SERVER_ERROR, 50007, "晨检消息处理失败")


async def list_device_records(
    db: AsyncSession,
    tenant_id: int,
    query: DeviceRecordQuery,
    current_user: User,
) -> Dict[str, Any]:
    visible_org_ids = await _visible_org_ids(db, current_user)
    if not visible_org_ids:
        return {"total": 0, "page": query.page, "page_size": query.page_size, "records": []}

    filters = [
        BizDeviceRecord.tenant_id == tenant_id,
        BizDeviceRecord.is_deleted.is_(False),
        BizDeviceRecord.org_id.in_(visible_org_ids),
    ]
    if query.start_date:
        filters.append(BizDeviceRecord.submit_date >= query.start_date)
    if query.end_date:
        filters.append(BizDeviceRecord.submit_date <= query.end_date)

    total_stmt = select(func.count()).select_from(BizDeviceRecord).where(*filters)
    total = (await db.execute(total_stmt)).scalar_one()

    stmt = (
        select(
            BizDeviceRecord,
            BizDevice.device_name,
            BizDevice.device_code,
            OrgModel.name.label("org_name"),
        )
        .join(
            BizDevice,
            (BizDeviceRecord.device_id == BizDevice.id)
            & (BizDevice.tenant_id == tenant_id)
            & (BizDevice.is_deleted.is_(False)),
        )
        .join(OrgModel, BizDeviceRecord.org_id == OrgModel.id)
        .where(*filters)
        .order_by(BizDeviceRecord.submit_date.desc(), BizDeviceRecord.id.desc())
        .offset((query.page - 1) * query.page_size)
        .limit(query.page_size)
    )
    rows = (await db.execute(stmt)).all()

    records = []
    for record, device_name, device_code, org_name in rows:
        record_type = _get_record_type(record.data_type)
        records.append(
            {
                "id": record.id,
                "org_name": org_name,
                "device_name": device_name,
                "device_code": device_code,
                "data_type": record.data_type,
                "data_type_label": DATA_TYPE_LABELS.get(record.data_type, record.data_type),
                "is_related_ledger": record.is_related_ledger,
                "submit_date": record.submit_date,
                "status": record.status,
                "source": record.source,
                "trace_id": record.trace_id,
                "process_result": record.process_result,
                "record_type": record_type.value,
            }
        )

    return {
        "total": total,
        "page": query.page,
        "page_size": query.page_size,
        "records": records,
    }


async def get_device_record_detail(
    db: AsyncSession,
    tenant_id: int,
    record_id: int,
    current_user: User,
) -> Dict[str, Any]:
    visible_org_ids = await _visible_org_ids(db, current_user)
    if not visible_org_ids:
        _raise_http_error(status.HTTP_404_NOT_FOUND, 40402, "设备消息记录不存在")

    stmt = (
        select(
            BizDeviceRecord,
            BizDevice.device_name,
            BizDevice.device_code,
            OrgModel.name.label("org_name"),
        )
        .join(
            BizDevice,
            (BizDeviceRecord.device_id == BizDevice.id)
            & (BizDevice.tenant_id == tenant_id)
            & (BizDevice.is_deleted.is_(False)),
        )
        .join(OrgModel, BizDeviceRecord.org_id == OrgModel.id)
        .where(
            BizDeviceRecord.id == record_id,
            BizDeviceRecord.tenant_id == tenant_id,
            BizDeviceRecord.is_deleted.is_(False),
            BizDeviceRecord.org_id.in_(visible_org_ids),
        )
    )
    row = (await db.execute(stmt)).one_or_none()
    if row is None:
        _raise_http_error(status.HTTP_404_NOT_FOUND, 40402, "设备消息记录不存在")
    record, device_name, device_code, org_name = row
    record_type = _get_record_type(record.data_type)
    payload = _safe_dict(record.payload)
    detail_json = _safe_dict(record.detail_json)
    record_data = _build_record_data(record.data_type, payload, detail_json)
    return {
        "id": record.id,
        "org_name": org_name,
        "device_name": device_name,
        "device_code": device_code,
        "data_type": record.data_type,
        "data_type_label": DATA_TYPE_LABELS.get(record.data_type, record.data_type),
        "is_related_ledger": record.is_related_ledger,
        "submit_date": record.submit_date,
        "status": record.status,
        "source": record.source,
        "trace_id": record.trace_id,
        "process_result": record.process_result,
        "created_at": record.created_at,
        "record_type": record_type.value,
        "record_data": record_data.model_dump() if record_data else None,
    }


async def get_device_tree(
    db: AsyncSession,
    tenant_id: int,
    current_user: User,
) -> list[Dict[str, Any]]:
    visible_canteen_ids = await _visible_org_ids(db, current_user)
    if not visible_canteen_ids:
        return []

    orgs = (
        await db.execute(
            select(OrgModel).where(OrgModel.tenant_id == tenant_id)
        )
    ).scalars().all()
    org_map = {org.id: org for org in orgs}

    included_org_ids: Set[int] = set()
    for canteen_id in visible_canteen_ids:
        current_id = canteen_id
        while current_id is not None and current_id in org_map:
            if current_id in included_org_ids:
                break
            included_org_ids.add(current_id)
            current_id = org_map[current_id].parent_id

    selected_orgs = [org for org in orgs if org.id in included_org_ids]
    node_map: Dict[int, Dict[str, Any]] = {}
    roots: list[Dict[str, Any]] = []

    for org in selected_orgs:
        node_map[org.id] = {
            "id": org.id,
            "name": org.name,
            "org_type": org.org_type,
            "parent_id": org.parent_id,
            "children": [],
            "devices": [],
        }

    for org in selected_orgs:
        node = node_map[org.id]
        if org.parent_id and org.parent_id in node_map:
            node_map[org.parent_id]["children"].append(node)
        else:
            roots.append(node)

    devices = (
        await db.execute(
            select(BizDevice).where(
                BizDevice.tenant_id == tenant_id,
                BizDevice.is_deleted.is_(False),
                BizDevice.org_id.in_(visible_canteen_ids),
            )
        )
    ).scalars().all()

    for device in devices:
        parent = node_map.get(device.org_id)
        if not parent:
            continue
        parent["devices"].append(
            {
                "id": device.id,
                "device_code": device.device_code,
                "device_name": device.device_name,
                "status": device.status,
                "last_heartbeat": device.last_heartbeat,
            }
        )

    return roots


async def update_device_record(
    db: AsyncSession,
    tenant_id: int,
    record_id: int,
    payload: Dict[str, Any],
    current_user: User,
) -> Dict[str, Any]:
    try:
        visible_org_ids = await _visible_org_ids(db, current_user)
        if not visible_org_ids:
            _raise_http_error(status.HTTP_404_NOT_FOUND, 40402, "设备消息记录不存在")

        record = (
            await db.execute(
                select(BizDeviceRecord).where(
                    BizDeviceRecord.id == record_id,
                    BizDeviceRecord.tenant_id == tenant_id,
                    BizDeviceRecord.is_deleted.is_(False),
                    BizDeviceRecord.org_id.in_(visible_org_ids),
                )
            )
        ).scalar_one_or_none()
        if record is None:
            _raise_http_error(status.HTTP_404_NOT_FOUND, 40402, "设备消息记录不存在")

        for key, value in payload.items():
            setattr(record, key, value)

        await db.commit()
        await db.refresh(record)

        return {
            "id": record.id,
            "is_related_ledger": record.is_related_ledger,
            "status": record.status,
            "updated_at": record.updated_at,
        }
    except HTTPException:
        await db.rollback()
        raise
    except SQLAlchemyError:
        await db.rollback()
        _raise_http_error(status.HTTP_500_INTERNAL_SERVER_ERROR, 50008, "编辑设备消息记录失败")


def _build_record_export_rows(records: list[Dict[str, Any]]) -> list[list[Any]]:
    rows: list[list[Any]] = []
    for record in records:
        rows.append(
            [
                record["id"],
                record.get("org_name") or "",
                record["device_name"],
                record["device_code"],
                record["data_type_label"],
                "是" if record["is_related_ledger"] else "否",
                str(record["submit_date"]),
                record["status"],
                record["source"],
                record["process_result"],
                record.get("trace_id") or "",
            ]
        )
    return rows


def _export_records_as_excel(headers: list[str], rows: list[list[Any]]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "设备消息记录"
    ws.append(headers)
    for row in rows:
        ws.append(row)

    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def _export_records_as_csv(headers: list[str], rows: list[list[Any]]) -> bytes:
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    return output.getvalue().encode("utf-8-sig")


def _export_records_as_pdf(headers: list[str], rows: list[list[Any]]) -> bytes:
    buffer = BytesIO()
    try:
        pdfmetrics.registerFont(TTFont("SimSun", r"C:/Windows/Fonts/simsun.ttc"))
        font_name = "SimSun"
    except Exception:
        font_name = "Helvetica"

    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setFont(font_name, 10)
    _, height = A4

    x_margin = 20
    y = height - 30
    line_height = 14

    pdf.drawString(x_margin, y, " | ".join(headers))
    y -= line_height

    for row in rows:
        if y < 30:
            pdf.showPage()
            pdf.setFont(font_name, 10)
            y = height - 30
        pdf.drawString(x_margin, y, " | ".join("" if v is None else str(v) for v in row))
        y -= line_height

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


async def export_device_records(
    db: AsyncSession,
    tenant_id: int,
    query: DeviceRecordExportQuery,
    current_user: User,
) -> Dict[str, Any]:
    list_query = DeviceRecordQuery(
        start_date=query.start_date,
        end_date=query.end_date,
        page=1,
        page_size=1000,
    )
    data = await list_device_records(
        db=db,
        tenant_id=tenant_id,
        query=list_query,
        current_user=current_user,
    )
    records = data["records"]

    headers = [
        "记录ID",
        "提交食堂",
        "设备名称",
        "设备编码",
        "设备数据类型",
        "是否关联电子台账",
        "提交日期",
        "设备状态",
        "来源",
        "处理结果",
        "追踪ID",
    ]
    rows = _build_record_export_rows(records)

    export_date = datetime.now(timezone.utc).strftime("%Y%m%d")
    if query.format == "excel":
        return {
            "filename": f"device_records_{export_date}.xlsx",
            "media_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "content": _export_records_as_excel(headers, rows),
        }
    if query.format == "pdf":
        return {
            "filename": f"device_records_{export_date}.pdf",
            "media_type": "application/pdf",
            "content": _export_records_as_pdf(headers, rows),
        }
    return {
        "filename": f"device_records_{export_date}.csv",
        "media_type": "text/csv",
        "content": _export_records_as_csv(headers, rows),
    }
