from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import List, Optional, Tuple

from fastapi import APIRouter, Depends, Path, Query, Request
from fastapi.responses import Response
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.context import UserContext
from app.db import get_db, get_sync_db
from app.modules.ledger.constants import LedgerStatus
from app.modules.ledger.models import LedgerInstance, LedgerTemplate
from app.modules.ledger.schemas import (
    GenericResponse,
    SOPTaskRequest,
    SOPTaskStatusRequest,
    SubmitRequest,
    TemplateRequest,
)
from app.modules.ledger.service import LedgerService, ReportService, SOPTaskService, TemplateService

router = APIRouter()


@router.get("/ledger/instances", response_model=GenericResponse)
def get_ledger_instances(
    page: int = 1,
    size: int = 10,
    date: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_sync_db),
):
    """获取台账任务列表（分页）。"""

    query = db.query(LedgerInstance)

    if status:
        query = query.filter(LedgerInstance.status == status)

    if date:
        # TODO: add create_date filter when requirement finalized.
        pass

    total = query.count()
    records = query.offset((page - 1) * size).limit(size).all()

    records_data = [
        {
            "id": record.id,
            "canteen_id": record.canteen_id,
            "status": record.status,
            "created_at": record.create_time or record.create_date,
        }
        for record in records
    ]

    return GenericResponse(
        code=20000,
        msg="success",
        data={
            "total": total,
            "page": page,
            "size": size,
            "records": records_data,
        },
    )


@router.post("/ledger/instances/{id}/submit", response_model=GenericResponse)
def submit_ledger(
    submit_data: SubmitRequest,
    ledger_id: int = Path(..., ge=1, alias="id"),
    db: Session = Depends(get_sync_db),
):
    """签字提交台账。"""

    ledger = LedgerService.submit_ledger(db, ledger_id, submit_data.content)

    return GenericResponse(
        code=20000,
        msg="台账提交成功",
        data={
            "ledger_id": ledger.id,
            "status": ledger.status,
            "security_hash": ledger.security_hash,
        },
    )


@router.put("/ledger/instances/{id}/draft", response_model=GenericResponse)
def save_draft(
    submit_data: SubmitRequest,
    ledger_id: int = Path(..., ge=1, alias="id"),
    db: Session = Depends(get_sync_db),
):
    """暂存台账（支持幂等）。"""

    ledger = LedgerService.get_ledger(db, ledger_id)

    if ledger.status == LedgerStatus.SIGNED:
        return GenericResponse(
            code=40001,
            msg="重复提交",
            data={"ledger_id": ledger.id, "status": ledger.status},
        )

    filled_content = LedgerService.prepare_form_content(db, ledger, submit_data.content)

    ledger.content = filled_content
    ledger.status = LedgerStatus.FILLING

    db.commit()
    db.refresh(ledger)

    return GenericResponse(
        code=20000,
        msg="台账暂存成功",
        data={"ledger_id": ledger.id, "status": ledger.status},
    )


@router.get("/ledger/instances/{id}/verify", response_model=GenericResponse)
def verify_ledger(
    ledger_id: int = Path(..., ge=1, alias="id"),
    db: Session = Depends(get_sync_db),
):
    """验证台账完整性。"""

    is_valid = LedgerService.verify_ledger(db, ledger_id)

    return GenericResponse(
        code=20000,
        msg="台账验证成功" if is_valid else "台账验证失败",
        data={"ledger_id": ledger_id, "is_valid": is_valid},
    )


@router.put("/ledger/instances/{id}/archive", response_model=GenericResponse)
def archive_ledger(
    ledger_id: int = Path(..., ge=1, alias="id"),
    db: Session = Depends(get_sync_db),
):
    """归档台账。"""

    ledger = LedgerService.archive_ledger(db, ledger_id)

    return GenericResponse(
        code=20000,
        msg="台账归档成功",
        data={"ledger_id": ledger.id, "status": ledger.status},
    )


@router.get("/ledger/templates", response_model=GenericResponse)
def get_templates(
    page: int = 1,
    size: int = 10,
    db: Session = Depends(get_sync_db),
):
    """分页读取模板列表。"""

    result = TemplateService.get_templates(db, page, size)

    records_data = [
        {
            "id": template.id,
            "title": template.title,
            "description": template.description,
            "is_active": template.is_active,
            "created_at": template.create_time,
        }
        for template in result["records"]
    ]

    return GenericResponse(
        code=20000,
        msg="success",
        data={
            "total": result["total"],
            "page": result["page"],
            "size": result["size"],
            "records": records_data,
        },
    )


@router.post("/ledger/templates", response_model=GenericResponse)
def create_template(
    template_data: TemplateRequest,
    db: Session = Depends(get_sync_db),
):
    """创建模板。"""

    template = TemplateService.create_template(db, template_data.model_dump())

    return GenericResponse(
        code=20000,
        msg="模板创建成功",
        data={"id": template.id, "title": template.title, "schema": template.schema},
    )


@router.delete("/ledger/templates/{id}", response_model=GenericResponse)
def delete_template(
    template_id: int = Path(..., ge=1, alias="id"),
    db: Session = Depends(get_sync_db),
):
    """删除模板。"""

    TemplateService.delete_template(db, template_id)

    return GenericResponse(
        code=20000,
        msg="模板删除成功",
        data={"template_id": template_id},
    )


@router.put("/ledger/templates/{id}", response_model=GenericResponse)
async def update_template_full(
    request: Request,
    db: AsyncSession = Depends(get_db),
    template_id: int = Path(..., ge=1, alias="id"),
):
    """电子台账模板编辑页真实保存。

    支持更新 description、scope（覆盖范围）、extraConfig 字段。
    该接口按智慧食安平台通用规范实现。
    """
    from app.modules.user.schemas import UserInfo
    from app.modules.user.security import get_current_admin

    current_user: UserInfo = await get_current_admin(request)
    tenant_id = current_user.tenant_id or 1

    import json
    from app.modules.ledger.schemas import TemplateScopeRequest
    from app.modules.ledger.service import TemplateScopeService

    body = await request.json()
    scope_request = TemplateScopeRequest(**body)

    description = scope_request.description
    scope_data = scope_request.scope.model_dump() if scope_request.scope else None
    extra_config = None
    if scope_request.extra_config:
        extra_config = json.loads(scope_request.extra_config)

    template, scope = await TemplateScopeService.update_scope_full(
        db,
        template_id,
        tenant_id,
        description=description,
        scope_data=scope_data,
        extra_config=extra_config,
    )

    return GenericResponse(
        code=20000,
        msg="模板更新成功",
        data={
            "id": template.id,
            "title": template.title,
            "description": template.description,
            "scope": {
                "users": scope.user_ids if scope else [],
                "canteens": scope.canteen_ids if scope else [],
            },
            "extra_config": scope.extra_config if scope else None,
        },
    )


@router.get("/ledger/templates/{id}/scope", response_model=GenericResponse)
async def get_template_scope(
    request: Request,
    db: AsyncSession = Depends(get_db),
    template_id: int = Path(..., ge=1, alias="id"),
):
    """获取模板覆盖范围（人员、食堂）。

    该接口按智慧食安平台通用规范实现。
    """
    from app.modules.user.schemas import UserInfo
    from app.modules.user.security import get_current_admin

    current_user: UserInfo = await get_current_admin(request)
    tenant_id = current_user.tenant_id or 1

    from app.modules.ledger.service import TemplateScopeService

    scope = await TemplateScopeService.get_scope_by_template(db, template_id, tenant_id)

    if not scope:
        return GenericResponse(
            code=20000,
            msg="success",
            data={
                "template_id": template_id,
                "description": None,
                "users": [],
                "canteens": [],
                "extra_config": None,
            },
        )

    return GenericResponse(
        code=20000,
        msg="success",
        data={
            "template_id": template_id,
            "description": None,
            "users": scope.user_ids or [],
            "canteens": scope.canteen_ids or [],
            "extra_config": scope.extra_config,
        },
    )


@router.post("/ledger/templates/{id}/scope/users/batch", response_model=GenericResponse)
async def batch_update_scope_users(
    request: Request,
    db: AsyncSession = Depends(get_db),
    template_id: int = Path(..., ge=1, alias="id"),
):
    """批量覆盖人员。

    支持空数组清空覆盖范围。
    该接口按智慧食安平台通用规范实现。
    """
    from app.modules.user.schemas import UserInfo
    from app.modules.user.security import get_current_admin

    current_user: UserInfo = await get_current_admin(request)
    tenant_id = current_user.tenant_id or 1

    from app.modules.ledger.schemas import BatchScopeRequest
    from app.modules.ledger.service import TemplateScopeService

    body = await request.json()
    batch_request = BatchScopeRequest(**body)

    scope = await TemplateScopeService.update_scope_users(
        db, template_id, tenant_id, batch_request.ids
    )

    return GenericResponse(
        code=20000,
        msg="人员覆盖范围更新成功",
        data={
            "template_id": template_id,
            "updated_count": len(batch_request.ids),
            "scope": {
                "users": scope.user_ids or [],
                "canteens": scope.canteen_ids or [],
            },
        },
    )


@router.post("/ledger/templates/{id}/scope/canteens/batch", response_model=GenericResponse)
async def batch_update_scope_canteens(
    request: Request,
    db: AsyncSession = Depends(get_db),
    template_id: int = Path(..., ge=1, alias="id"),
):
    """批量覆盖食堂。

    支持空数组清空覆盖范围。
    该接口按智慧食安平台通用规范实现。
    """
    from app.modules.user.schemas import UserInfo
    from app.modules.user.security import get_current_admin

    current_user: UserInfo = await get_current_admin(request)
    tenant_id = current_user.tenant_id or 1

    from app.modules.ledger.schemas import BatchScopeRequest
    from app.modules.ledger.service import TemplateScopeService

    body = await request.json()
    batch_request = BatchScopeRequest(**body)

    scope = await TemplateScopeService.update_scope_canteens(
        db, template_id, tenant_id, batch_request.ids
    )

    return GenericResponse(
        code=20000,
        msg="食堂覆盖范围更新成功",
        data={
            "template_id": template_id,
            "updated_count": len(batch_request.ids),
            "scope": {
                "users": scope.user_ids or [],
                "canteens": scope.canteen_ids or [],
            },
        },
    )


@router.post("/ledger/tasks", response_model=GenericResponse)
def create_sop_task(
    task_data: SOPTaskRequest,
    db: Session = Depends(get_sync_db),
):
    """创建 SOP 任务。"""

    task = SOPTaskService.create_task(db, task_data.model_dump())

    return GenericResponse(
        code=20000,
        msg="任务创建成功",
        data={
            "id": task.id,
            "name": task.name,
            "template_id": task.template_id,
            "cron_expression": task.cron_expression,
            "scope": task.scope,
        },
    )


@router.put("/ledger/tasks/{id}/status", response_model=GenericResponse)
def update_sop_task_status(
    status_data: SOPTaskStatusRequest,
    db: Session = Depends(get_sync_db),
    task_id: int = Path(..., ge=1, alias="id"),
):
    """更新 SOP 任务状态。"""

    task = SOPTaskService.update_task_status(db, task_id, status_data.is_active)

    return GenericResponse(
        code=20000,
        msg="任务状态更新成功",
        data={"id": task.id, "name": task.name, "is_active": task.is_active},
    )


def _normalize_date_range(start_date: datetime, end_date: datetime) -> Tuple[datetime, datetime]:
    start = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    return start, end


def _build_schema_headers(schema_snapshot: Optional[dict]) -> Tuple[List[str], List[str]]:
    fields: List[dict] = []
    field_ids: List[str] = []
    if schema_snapshot and isinstance(schema_snapshot, dict):
        fields = schema_snapshot.get("fields") or []

    headers: List[str] = []
    for field in fields:
        if not isinstance(field, dict):
            continue
        field_id = field.get("field_id") or field.get("id")
        if not field_id:
            continue
        label = field.get("label") or field_id
        headers.append(label)
        field_ids.append(field_id)

    return headers, field_ids


def _maybe_tenant_filter() -> Optional[int]:
    tenant_id = UserContext.get_tenant_id()
    if not tenant_id:
        return None
    try:
        return int(tenant_id)
    except (TypeError, ValueError):
        return None


@router.get("/report/compilation", response_model=GenericResponse)
async def get_compilation_report(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    canteen_id: Optional[int] = Query(None, description="Canteen ID"),
    task_type: Optional[str] = Query(None, description="Task type"),
    db: AsyncSession = Depends(get_db),
):
    del task_type

    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return GenericResponse(code=40000, msg="日期格式错误", data=None)

    start_dt, end_dt = _normalize_date_range(start, end)

    filters = [LedgerInstance.create_date >= start_dt, LedgerInstance.create_date <= end_dt]

    tenant_id = _maybe_tenant_filter()
    if tenant_id is not None:
        filters.append(LedgerInstance.tenant_id == tenant_id)

    if canteen_id is not None:
        filters.append(LedgerInstance.canteen_id == canteen_id)

    status_columns = [
        func.sum(case((LedgerInstance.status == status.value, 1), else_=0)).label(status.value)
        for status in LedgerStatus
    ]

    stmt = select(func.count().label("total"), *status_columns).where(*filters)
    result = await db.execute(stmt)
    row = result.one()
    mapping = row._mapping

    total_tasks = int(mapping.get("total") or 0)
    status_stats = {status.value: int(mapping.get(status.value) or 0) for status in LedgerStatus}

    completed_statuses = {LedgerStatus.SIGNED.value, LedgerStatus.ARCHIVED.value}
    completed_tasks = sum(status_stats.get(status, 0) for status in completed_statuses)
    completion_rate = round(completed_tasks / total_tasks * 100, 2) if total_tasks else 0

    return GenericResponse(
        code=20000,
        msg="success",
        data={
            "completion_rate": completion_rate,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "status_stats": status_stats,
        },
    )


@router.get("/report/export")
async def export_report(
    request: Request,
    date: str = Query(..., description="Export date (YYYY-MM-DD)"),
    template_id: Optional[int] = Query(None, description="Template ID"),
    canteen_id: Optional[int] = Query(None, description="Canteen ID"),
    status: Optional[str] = Query(None, description="Status filter"),
    format: str = Query("excel", description="Export format (excel/pdf)"),
    db: AsyncSession = Depends(get_db),
):
    try:
        export_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return GenericResponse(code=40002, msg="invalid date format, expect yyyy-MM-dd", data=None)

    if status:
        valid_statuses = {item.value for item in LedgerStatus}
        if status not in valid_statuses:
            return GenericResponse(
                code=40002,
                msg="invalid status value, expect one of PENDING/FILLING/SIGNED/ARCHIVED",
                data=None,
            )

    if not template_id:
        return GenericResponse(
            code=40004,
            msg="export requires a single template, please specify template_id",
            data=None,
        )

    filters = [LedgerInstance.template_id == template_id]
    tenant_id = _maybe_tenant_filter()
    if tenant_id is not None:
        filters.append(LedgerInstance.tenant_id == tenant_id)

    if canteen_id is not None:
        filters.append(LedgerInstance.canteen_id == canteen_id)

    if status:
        filters.append(LedgerInstance.status == status)

    start_of_day, end_of_day = _normalize_date_range(export_date, export_date)
    filters.extend(
        [LedgerInstance.create_date >= start_of_day, LedgerInstance.create_date <= end_of_day]
    )

    stmt = select(LedgerInstance).where(*filters)
    result = await db.execute(stmt)
    ledgers = result.scalars().all()

    if len(ledgers) > 1000:
        return GenericResponse(code=40003, msg="too many records to export, limit is 1000", data=None)

    output = io.StringIO()
    writer = csv.writer(output)

    schema_headers: List[str] = []
    schema_field_ids: List[str] = []
    if ledgers:
        schema_headers, schema_field_ids = _build_schema_headers(ledgers[0].schema_snapshot)

    base_headers = ["台账ID", "食堂ID", "状态", "创建时间", "提交时间"]
    writer.writerow(base_headers + schema_headers)

    for ledger in ledgers:
        created_at = ledger.create_time or ledger.create_date
        submit_time = ledger.submit_time
        status_value = (
            ledger.status.value if isinstance(ledger.status, LedgerStatus) else ledger.status
        )
        row = [
            ledger.id,
            ledger.canteen_id,
            status_value,
            created_at.strftime("%Y-%m-%d %H:%M:%S") if created_at else "",
            submit_time.strftime("%Y-%m-%d %H:%M:%S") if submit_time else "",
        ]

        content = ledger.content or {}
        for field_id in schema_field_ids:
            row.append(content.get(field_id, ""))

        writer.writerow(row)

    output.seek(0)
    csv_content = output.getvalue()

    try:
        user_id = UserContext.get_user_id() or "anonymous"
        tenant_for_log = UserContext.get_tenant_id() or str(tenant_id or "0")
        ip_address = request.client.host if request.client else ""
        user_agent = request.headers.get("user-agent", "")

        await ReportService.record_export_log_async(
            db=db,
            user_id=str(user_id),
            tenant_id=str(tenant_for_log),
            export_date=date,
            template_id=template_id,
            canteen_id=str(canteen_id) if canteen_id is not None else None,
            format=format,
            record_count=len(ledgers),
            ip_address=ip_address,
            user_agent=user_agent,
        )
    except Exception:
        pass

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=report_{date}.csv"},
    )
