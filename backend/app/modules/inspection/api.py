from datetime import date, datetime, timezone
from typing import List, Optional
import base64
import hashlib
import hmac
import os
import shutil
from urllib.parse import quote

from fastapi import APIRouter, Depends, Header, HTTPException, Body, Path, Query, Request, status, UploadFile, File, Form
from fastapi.responses import Response, FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.constants.permissions import (
    DAILY_APPROVE,
    DAILY_CREATE_TEMPLATE,
    DAILY_PUBLISH,
    DAILY_SUBMIT,
    DAILY_VIEW,
    WEEKLY_APPROVE_RECTIFY,
    WEEKLY_CREATE_TEMPLATE,
    WEEKLY_PUBLISH,
    WEEKLY_RECTIFY,
    WEEKLY_SUBMIT,
    WEEKLY_VIEW,
    MONTHLY_VIEW_REPORT,
    MONTHLY_DOWNLOAD_REPORT,
    MONTHLY_UPLOAD_REPORT,
    MONTHLY_DELETE_REPORT,
    JOINT_CREATE_TEMPLATE,
    JOINT_PUBLISH,
    JOINT_SUBMIT,
    JOINT_VIEW,
    JOINT_RECTIFY,
    JOINT_APPROVE,
    JOINT_SIGN,
)
from app.core.deps import get_current_user
from app.core.enums import InspectionTaskStatus
from app.db.session import get_db
from app.modules.inspection.models import (
    InspectionItem,
    InspectionResult,
    InspectionTask,
    InspectionTemplate,
    InspectionType,
    ItemType,
    MonthlyReport,
)
from app.modules.inspection.schemas import (
    DailyControlSubmitRequest,
    DailyRectifyRequest,
    DailyTemplateRequest,
    TemplateStatusRequest,
    WeeklyDispatchRequest,
    WeeklyInspectionSubmitRequest,
    WeeklyRectifyRequest,
    WeeklySnapshotUpdateRequest,
    WeeklyTemplateRequest,
    MonthlyReportPreviewRequest,
    MonthlyReportExportRequest,
    MonthlyReportUploadRequest,
    MonthlyReportPreviewResponse,
    JointSignRequest,
    MonthlyReportFileUploadResponse,
)
from app.modules.inspection.service import (
    InspectionService,
    InspectionTemplateService,
    InspectionWorkflow,
    JointInspectionService,
    MonthlyReportService,
)
from app.modules.user.models import Org, User
from app.modules.user.service import get_permissions_for_user

router = APIRouter()


class GenericResponse(BaseModel):
    code: int
    msg: str
    request_id: Optional[str] = None
    data: Optional[dict] = None


class ItemScoreEntry(BaseModel):
    result_id: int
    score: float = Field(..., ge=0)


class AuditRequest(BaseModel):
    auditor_id: str
    action: str = Field(..., pattern="^(PASS|REJECT)$")
    opinion: Optional[str] = None
    item_scores: Optional[List[ItemScoreEntry]] = None


def _to_utc_iso(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.isoformat().replace("+00:00", "Z")


def _status_text(status: str) -> str:
    mapping = {
        "PENDING": "待整改",
        "SUBMITTED": "待审核",
        "REJECTED": "待整改",
        "RECTIFIED": "待审核",
        "COMPLETED": "已完成",
        "CANCELLED": "已取消",
    }
    return mapping.get(status, status)


def _raw_target_node_ids(value: Optional[dict]) -> List[int]:
    if isinstance(value, dict):
        raw = value.get("raw")
        if isinstance(raw, list):
            return [item for item in raw if isinstance(item, int)]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, int)]
    return []


def _expanded_target_node_ids(value: Optional[dict]) -> List[int]:
    """Return expanded canteen-level IDs, falling back to raw IDs."""
    if isinstance(value, dict):
        expanded = value.get("expanded_canteen_ids")
        if isinstance(expanded, list) and expanded:
            return [item for item in expanded if isinstance(item, int)]
        raw = value.get("raw")
        if isinstance(raw, list):
            return [item for item in raw if isinstance(item, int)]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, int)]
    return []


async def _ensure_permission(
    db: AsyncSession,
    user: User,
    permission: str,
    msg: str,
) -> None:
    permissions = await get_permissions_for_user(db, user)
    if permission not in permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": 40300, "msg": msg, "data": None},
        )


async def _ensure_any_permission(
    db: AsyncSession,
    user: User,
    *required: str,
    msg: str = "无权限",
) -> None:
    permissions = await get_permissions_for_user(db, user)
    if not any(p in permissions for p in required):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": 40300, "msg": msg, "data": None},
        )


_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_MONTHLY_REPORT_FILE_DIR = os.path.join(_BACKEND_DIR, "monthly_reports")
os.makedirs(_MONTHLY_REPORT_FILE_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".jpg", ".png"}
MAX_FILE_SIZE = 50 * 1024 * 1024

def _get_base_url(request) -> str:
    configured = (settings.public_base_url or "").strip()
    if configured:
        return configured.rstrip("/")
    return str(request.base_url).rstrip("/")


def _encode_public_file_token(file_key: str, expires_at: int) -> str:
    payload = f"{file_key}:{expires_at}"
    digest = hmac.new(
        settings.jwt_secret_key.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    raw = f"{payload}:{digest}".encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _decode_public_file_token(token: str) -> tuple[str, int]:
    padding = "=" * ((4 - len(token) % 4) % 4)
    try:
        decoded = base64.urlsafe_b64decode((token + padding).encode("utf-8")).decode("utf-8")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的访问令牌")
    parts = decoded.split(":")
    if len(parts) != 3:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的访问令牌")
    file_key_raw, expires_at_raw, digest = parts
    payload = f"{file_key_raw}:{expires_at_raw}"
    expected = hmac.new(
        settings.jwt_secret_key.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(digest, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的访问令牌")
    expires_at = int(expires_at_raw)
    if int(datetime.now().timestamp()) > expires_at:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="访问令牌已过期")
    return file_key_raw, expires_at


def _build_signed_public_url(base_url: str, file_key: str, expires_in_seconds: int) -> tuple[str, int]:
    expires_at = int(datetime.now().timestamp()) + expires_in_seconds
    token = _encode_public_file_token(file_key, expires_at)
    return f"{base_url}/files/monthly-reports/public/{token}", expires_at


@router.get("/daily-controls/templates", response_model=GenericResponse)
async def list_daily_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    canteen_id: Optional[int] = Query(None, description="按食堂ID过滤"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_any_permission(db, current_user, DAILY_VIEW, DAILY_SUBMIT, msg='无查看日管控模板权限')
    result = await InspectionTemplateService.list_templates(
        db, current_user.tenant_id, InspectionType.DAILY, page, page_size
    )
    items = []
    for template in result["records"]:
        items.append(
            {
                "id": template.id,
                "template_name": template.template_name,
                "executor_role": template.executor_role,
                "approver_role": template.approver_role,
                "start_time": template.start_time,
                "end_time": template.end_time,
                "is_active": template.is_active,
                "target_node_ids": _raw_target_node_ids(template.target_node_ids_raw),
                "created_at": _to_utc_iso(template.created_at),
                "updated_at": _to_utc_iso(template.updated_at),
            }
        )
    return GenericResponse(
        code=20000,
        msg="success",
        data={"total": result["total"], "list": items},
    )


@router.post("/daily-controls/templates", response_model=GenericResponse)
async def create_daily_template(
    request: DailyTemplateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, DAILY_CREATE_TEMPLATE, "�޴����չܿ�ģ��Ȩ��")
    template = await InspectionTemplateService.create_daily_template(
        db, current_user, request
    )
    return GenericResponse(
        code=20000,
        msg="success",
        data={"id": template.id},
    )


@router.get("/daily-controls/templates/{template_id}", response_model=GenericResponse)
async def get_daily_template(
    template_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_any_permission(db, current_user, DAILY_VIEW, DAILY_SUBMIT, msg='无查看日管控模板权限')
    template = await InspectionTemplateService.get_template(
        db, current_user.tenant_id, template_id, InspectionType.DAILY
    )
    items = []
    for item in sorted(
        [
            i
            for i in template.items
            if i.parent_item_id is None and i.item_type == ItemType.ITEM
        ],
        key=lambda x: x.sort_order,
    ):
        items.append(
            {
                "item_id": item.id,
                "sort_order": item.sort_order,
                "content": item.content,
                "completion_method": item.completion_method,
                "is_active": item.is_active,
            }
        )
    data = {
        "id": template.id,
        "template_name": template.template_name,
        "executor_role": template.executor_role,
        "approver_role": template.approver_role,
        "start_time": template.start_time,
        "end_time": template.end_time,
        "target_node_ids": _raw_target_node_ids(template.target_node_ids_raw),
        "items": items,
        "is_active": template.is_active,
        "created_at": _to_utc_iso(template.created_at),
        "updated_at": _to_utc_iso(template.updated_at),
    }
    return GenericResponse(code=20000, msg="success", data=data)


@router.put("/daily-controls/templates/{template_id}", response_model=GenericResponse)
async def update_daily_template(
    request: DailyTemplateRequest,
    template_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, DAILY_CREATE_TEMPLATE, "�ޱ༭�չܿ�ģ��Ȩ��")
    template = await InspectionTemplateService.update_daily_template(
        db, template_id, current_user, request
    )
    return GenericResponse(
        code=20000,
        msg="success",
        data={"id": template.id},
    )


@router.patch("/daily-controls/templates/{template_id}/status", response_model=GenericResponse)
async def update_daily_template_status(
    request: TemplateStatusRequest,
    template_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, DAILY_PUBLISH, "�޷����չܿ�ģ��Ȩ��")
    template = await InspectionTemplateService.update_template_status(
        db, current_user.tenant_id, template_id, InspectionType.DAILY, request.is_active
    )
    return GenericResponse(
        code=20000,
        msg="success",
        data={"id": template.id, "is_active": template.is_active},
    )


@router.delete("/daily-controls/templates/{template_id}", response_model=GenericResponse)
async def delete_daily_template(
    template_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, DAILY_CREATE_TEMPLATE, "��ɾ���չܿ�ģ��Ȩ��")
    await InspectionTemplateService.delete_template(
        db, current_user.tenant_id, template_id, InspectionType.DAILY
    )
    return GenericResponse(code=20000, msg="success", data={"id": template_id})


def _snapshot_stats(form_snapshot) -> tuple:
    """从 form_snapshot 中统计满分总和、实际得分、红线项数、黄线项数。"""
    max_score = 0.0
    actual_score = 0.0
    red_count = 0
    yellow_count = 0
    if isinstance(form_snapshot, dict):
        for major in form_snapshot.get("major_items", []):
            for minor in major.get("minor_items", []):
                max_score += float(minor.get("total_score") or 0)
                actual_score += float(minor.get("score_given") or 0)
                issue_type = minor.get("issue_type") or ""
                if issue_type == "红线":
                    red_count += 1
                elif issue_type == "黄线":
                    yellow_count += 1
    return max_score, actual_score, red_count, yellow_count


@router.get("/weekly-inspections/templates", response_model=GenericResponse)
async def list_weekly_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    canteen_id: Optional[int] = Query(None, description="按食堂ID过滤"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, WEEKLY_VIEW, "�޲鿴���Ų�ģ��Ȩ��")
    result = await InspectionTemplateService.list_templates(
        db, current_user.tenant_id, InspectionType.WEEKLY, page, page_size
    )

    # 批量获取每个模板的小项统计（minor item count, red/yellow line counts, max score）
    template_ids = [t.id for t in result["records"]]
    template_stats: dict = {}
    if template_ids:
        stat_rows = (
            await db.execute(
                select(
                    InspectionItem.template_id,
                    InspectionItem.issue_type,
                    InspectionItem.total_score,
                ).where(
                    InspectionItem.template_id.in_(template_ids),
                    InspectionItem.item_type == ItemType.ITEM,
                )
            )
        ).all()
        for row in stat_rows:
            tid = row[0]
            if tid not in template_stats:
                template_stats[tid] = {"minor_count": 0, "red_count": 0, "yellow_count": 0, "max_score": 0.0}
            template_stats[tid]["minor_count"] += 1
            template_stats[tid]["max_score"] += float(row[2] or 0)
            if row[1] == "红线":
                template_stats[tid]["red_count"] += 1
            elif row[1] == "黄线":
                template_stats[tid]["yellow_count"] += 1

    items = []
    for template in result["records"]:
        stats = template_stats.get(template.id, {"minor_count": 0, "red_count": 0, "yellow_count": 0, "max_score": 0.0})
        items.append(
            {
                "id": template.id,
                "template_name": template.template_name,
                "executor_role": template.executor_role,
                "approver_role": template.approver_role,
                "form_type": template.form_type,
                "start_time": template.start_time,
                "end_time": template.end_time,
                "is_active": template.is_active,
                "target_node_ids": _raw_target_node_ids(template.target_node_ids_raw),
                "created_at": _to_utc_iso(template.created_at),
                "updated_at": _to_utc_iso(template.updated_at),
                "minor_item_count": stats["minor_count"],
                "red_line_count": stats["red_count"],
                "yellow_line_count": stats["yellow_count"],
                "max_score": stats["max_score"],
            }
        )
    return GenericResponse(
        code=20000,
        msg="success",
        data={"total": result["total"], "list": items},
    )


@router.post("/weekly-inspections/templates", response_model=GenericResponse)
async def create_weekly_template(
    request: WeeklyTemplateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, WEEKLY_CREATE_TEMPLATE, "�޴������Ų�ģ��Ȩ��")
    template = await InspectionTemplateService.create_weekly_template(
        db, current_user, request
    )
    return GenericResponse(
        code=20000,
        msg="success",
        data={"id": template.id},
    )


@router.get("/weekly-inspections/templates/{template_id}", response_model=GenericResponse)
async def get_weekly_template(
    template_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, WEEKLY_VIEW, "�޲鿴���Ų�ģ��Ȩ��")
    template = await InspectionTemplateService.get_template(
        db, current_user.tenant_id, template_id, InspectionType.WEEKLY
    )
    groups = [i for i in template.items if i.item_type == ItemType.GROUP]
    children_map = {}
    for item in template.items:
        if item.parent_item_id:
            children_map.setdefault(item.parent_item_id, []).append(item)
    major_items = []
    for group in sorted(groups, key=lambda x: x.sort_order):
        minor_items = []
        for minor in sorted(children_map.get(group.id, []), key=lambda x: x.sort_order):
            minor_items.append(
                {
                    "item_id": minor.id,
                    "sort_order": minor.sort_order,
                    "content": minor.content,
                    "issue_type": minor.issue_type,
                    "total_score": minor.total_score,
                    "scoring_options": minor.scoring_options,
                    "is_active": minor.is_active,
                }
            )
        major_items.append(
            {
                "title": group.content,
                "sort_order": group.sort_order,
                "minor_items": minor_items,
            }
        )
    node_ids = _expanded_target_node_ids(template.target_node_ids_raw)
    target_node_names: dict = {}
    if node_ids:
        orgs = (
            await db.execute(
                select(Org).where(
                    Org.id.in_(node_ids),
                    Org.tenant_id == current_user.tenant_id,
                )
            )
        ).scalars().all()
        target_node_names = {org.id: org.name for org in orgs}
    data = {
        "id": template.id,
        "template_name": template.template_name,
        "executor_role": template.executor_role,
        "approver_role": template.approver_role,
        "form_type": template.form_type,
        "start_time": template.start_time,
        "end_time": template.end_time,
        "target_node_ids": node_ids,
        "target_node_names": target_node_names,
        "major_items": major_items,
        "is_active": template.is_active,
        "created_at": _to_utc_iso(template.created_at),
        "updated_at": _to_utc_iso(template.updated_at),
    }
    return GenericResponse(code=20000, msg="success", data=data)


@router.put("/weekly-inspections/templates/{template_id}", response_model=GenericResponse)
async def update_weekly_template(
    request: WeeklyTemplateRequest,
    template_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, WEEKLY_CREATE_TEMPLATE, "�ޱ༭���Ų�ģ��Ȩ��")
    template = await InspectionTemplateService.update_weekly_template(
        db, template_id, current_user, request
    )
    return GenericResponse(
        code=20000,
        msg="success",
        data={"id": template.id},
    )


@router.patch("/weekly-inspections/templates/{template_id}/status", response_model=GenericResponse)
async def update_weekly_template_status(
    request: TemplateStatusRequest,
    template_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, WEEKLY_PUBLISH, "�޷������Ų�ģ��Ȩ��")
    template = await InspectionTemplateService.update_template_status(
        db, current_user.tenant_id, template_id, InspectionType.WEEKLY, request.is_active
    )
    return GenericResponse(
        code=20000,
        msg="success",
        data={"id": template.id, "is_active": template.is_active},
    )


@router.delete("/weekly-inspections/templates/{template_id}", response_model=GenericResponse)
async def delete_weekly_template(
    template_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, WEEKLY_CREATE_TEMPLATE, "��ɾ�����Ų�ģ��Ȩ��")
    await InspectionTemplateService.delete_template(
        db, current_user.tenant_id, template_id, InspectionType.WEEKLY
    )
    return GenericResponse(code=20000, msg="success", data={"id": template_id})


@router.post("/daily-controls/tasks/start", response_model=GenericResponse)
async def start_daily_task_from_template(
    template_id: int = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """��ģ��Ϊ��ǰ�û����������չܿ������ݵȣ������� task_id"""
    today = date.today()

    # ���ҽ����Ƿ����д�ģ��� PENDING ����
    stmt = (
        select(InspectionTask)
        .where(
            InspectionTask.template_id == template_id,
            InspectionTask.business_date == today,
            InspectionTask.inspection_type == InspectionType.DAILY,
            InspectionTask.tenant_id == current_user.tenant_id,
        )
    )
    if current_user.org_id:
        stmt = stmt.where(InspectionTask.canteen_id == current_user.org_id)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        return GenericResponse(
            code=20000,
            msg="success",
            data={"task_id": existing.id, "status": existing.status.value if hasattr(existing.status, 'value') else str(existing.status)},
        )

    # ����ģ�弰������
    tpl_stmt = (
        select(InspectionTemplate)
        .where(
            InspectionTemplate.id == template_id,
            InspectionTemplate.tenant_id == current_user.tenant_id,
        )
        .options(selectinload(InspectionTemplate.items))
    )
    tpl_result = await db.execute(tpl_stmt)
    template = tpl_result.scalar_one_or_none()
    if not template:
        raise HTTPException(
            status_code=404,
            detail={"code": 40400, "msg": "ģ�岻����", "data": None},
        )

    # ��ȡʳ������
    canteen_id = current_user.org_id or 0
    canteen_name = "δ֪ʳ��"
    if current_user.org_id:
        org = await db.get(Org, current_user.org_id)
        if org:
            canteen_name = org.name

    # ���� form_snapshot
    sorted_items = sorted(template.items, key=lambda x: (x.sort_order or 0))
    form_snapshot = [
        {"item_id": item.id, "content": item.content}
        for item in sorted_items
    ]

    new_task = InspectionTask(
        inspection_type=InspectionType.DAILY,
        template_id=template.id,
        business_date=today,
        canteen_id=canteen_id,
        canteen_name_snapshot=canteen_name,
        executor_name_snapshot=current_user.real_name or current_user.username,
        status=InspectionTaskStatus.PENDING,
        form_snapshot=form_snapshot,
        tenant_id=current_user.tenant_id,
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    return GenericResponse(
        code=20000,
        msg="success",
        data={"task_id": new_task.id, "status": "PENDING"},
    )


@router.get("/daily-controls/tasks", response_model=GenericResponse)
async def list_daily_tasks(
    start_date: Optional[str] = Query(None, description="��ʼ���ڣ�YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="�������ڣ�YYYY-MM-DD"),
    status: Optional[str] = Query(None, description="����״̬"),
    keyword: Optional[str] = Query(None, description="�����ؼ��֣�ʳ��/�ύ��/ģ�壩"),
    canteen_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, DAILY_VIEW, "无查看日管控任务权限")
    filters = [InspectionTask.inspection_type == InspectionType.DAILY]

    if start_date:
        filters.append(InspectionTask.business_date >= start_date)
    if end_date:
        filters.append(InspectionTask.business_date <= end_date)
    if status:
        filters.append(InspectionTask.status == status)
    if canteen_id:
        filters.append(InspectionTask.canteen_id == canteen_id)
    if keyword:
        pattern = f"%{keyword}%"
        filters.append(
            or_(
                InspectionTask.canteen_name_snapshot.ilike(pattern),
                InspectionTask.executor_name_snapshot.ilike(pattern),
            )
        )

    count_stmt = select(func.count()).where(*filters)
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        select(InspectionTask)
        .where(*filters)
        .options(selectinload(InspectionTask.template))  # Ԥ���ع�������
        .order_by(InspectionTask.business_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    tasks: List[InspectionTask] = result.scalars().all()

    items = []
    for task in tasks:
        status_value = task.status.value if hasattr(task.status, "value") else str(task.status)
        completion_progress = None
        if task.total_items is not None and task.finished_items is not None:
            completion_progress = f"{task.finished_items}/{task.total_items}"

        submission_date = None
        if task.submission_time is not None:
            submission_date = task.submission_time.date().isoformat()

        template_name = task.template.template_name if task.template is not None else None

        items.append(
            {
                "task_id": task.id,
                "template_id": task.template_id,
                "canteen_name": task.canteen_name_snapshot,
                "submitter_name": task.executor_name_snapshot,
                "template_name": template_name,
                "completion_progress": completion_progress,
                "submission_date": submission_date,
                "status": status_value,
                "status_text": _status_text(status_value),
            }
        )

    return GenericResponse(
        code=20000,
        msg="success",
        data={"total": total, "list": items},
    )


@router.get("/daily-controls/tasks/{task_id}", response_model=GenericResponse)
async def get_daily_task_detail(
    task_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, DAILY_VIEW, "无查看日管控任务权限")
    stmt = select(InspectionTask).where(
        InspectionTask.id == task_id,
        InspectionTask.inspection_type == InspectionType.DAILY,
    )
    result = await db.execute(stmt)
    task: Optional[InspectionTask] = result.scalar_one_or_none()
    if not task:
        return GenericResponse(code=40400, msg="���񲻴���", data=None)

    status_value = task.status.value if hasattr(task.status, "value") else str(task.status)

    result_stmt = select(InspectionResult).where(InspectionResult.task_id == task_id)
    result_rows = await db.execute(result_stmt)
    result_list: List[InspectionResult] = result_rows.scalars().all()
    result_map = {str(result.item_id): result for result in result_list}

    form_snapshot = task.form_snapshot
    if isinstance(form_snapshot, list):
        merged_snapshot = []
        for item in form_snapshot:
            item_data = dict(item)
            result = result_map.get(str(item_data.get("item_id")))
            if result:
                item_data["result_id"] = result.id
                item_data["is_qualified"] = bool(result.is_qualified) if result.is_qualified is not None else None
                item_data["description"] = result.inspection_description
                item_data["photos"] = result.inspection_photos
                item_data["rectification_photos"] = result.rectification_photos or []
                item_data["rectification_description"] = result.rectification_description
            merged_snapshot.append(item_data)
        form_snapshot = merged_snapshot

    task_info = {
        "task_id": task.id,
        "canteen_name": task.canteen_name_snapshot,
        "inspector_name": task.executor_name_snapshot,
        "inspector_id": task.inspector_id,
        "actual_start_time": _to_utc_iso(task.actual_start_time),
        "submission_date": _to_utc_iso(task.submission_time),
        "status": status_value,
        "status_text": _status_text(status_value),
    }

    return GenericResponse(
        code=20000,
        msg="success",
        data={
            "task_info": task_info,
            "form_snapshot": form_snapshot,
            "audit_logs": task.audit_logs or [],
        },
    )


@router.post("/weekly-inspections/tasks/dispatch", response_model=GenericResponse)
async def dispatch_weekly_tasks(
    request: WeeklyDispatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """监管端将周排查模板下发给指定食堂，为每个食堂创建一个 PENDING 的巡检任务。
    若该食堂在该日期的同模板任务已存在则跳过（幂等）。
    """
    await _ensure_permission(db, current_user, WEEKLY_PUBLISH, "无下发周排查权限")

    from datetime import date as date_cls
    try:
        biz_date = date_cls.fromisoformat(request.business_date)
    except ValueError:
        raise HTTPException(status_code=400, detail={"code": 40000, "msg": "business_date 格式错误，须为 YYYY-MM-DD", "data": None})

    # 加载模板及其检查项
    tpl_stmt = (
        select(InspectionTemplate)
        .where(
            InspectionTemplate.id == request.template_id,
            InspectionTemplate.tenant_id == current_user.tenant_id,
            InspectionTemplate.inspection_type == InspectionType.WEEKLY,
        )
        .options(selectinload(InspectionTemplate.items))
    )
    tpl_result = await db.execute(tpl_stmt)
    template = tpl_result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail={"code": 40400, "msg": "周排查模板不存在", "data": None})

    # 构建 form_snapshot（以字典形式，保留 major→minor 层级）
    group_items = sorted(
        [item for item in template.items if item.item_type == ItemType.GROUP],
        key=lambda x: (x.sort_order or 0),
    )
    major_items = []
    for group in group_items:
        minor_list = sorted(
            [item for item in template.items if item.parent_item_id == group.id],
            key=lambda x: (x.sort_order or 0),
        )
        major_items.append({
            "item_id": group.id,
            "title": group.content,
            "sort_order": group.sort_order or 0,
            "minor_items": [
                {
                    "item_id": minor.id,
                    "content": minor.content,
                    "issue_type": minor.issue_type,
                    "total_score": minor.total_score,
                    "scoring_options": minor.scoring_options or [],
                    "sort_order": minor.sort_order or 0,
                }
                for minor in minor_list
            ],
        })
    form_snapshot = {"major_items": major_items}

    # 若前端提供了预填写的快照，直接使用（覆盖自动生成的）
    if request.form_snapshot:
        form_snapshot = request.form_snapshot

    created_ids: list[int] = []
    skipped_ids: list[int] = []

    for canteen_id in request.canteen_ids:
        # 幂等检查
        exist_stmt = select(InspectionTask).where(
            InspectionTask.template_id == template.id,
            InspectionTask.business_date == biz_date,
            InspectionTask.inspection_type == InspectionType.WEEKLY,
            InspectionTask.tenant_id == current_user.tenant_id,
            InspectionTask.canteen_id == canteen_id,
        )
        existing = (await db.execute(exist_stmt)).scalar_one_or_none()
        if existing:
            # 若提供了新的预填快照且任务仍处于待提交状态，更新快照
            if form_snapshot and existing.status == InspectionTaskStatus.PENDING:
                existing.form_snapshot = form_snapshot
                db.add(existing)
            skipped_ids.append(existing.id)
            continue

        # 查食堂名称
        org = await db.get(Org, canteen_id)
        canteen_name = org.name if org else f"食堂{canteen_id}"

        new_task = InspectionTask(
            inspection_type=InspectionType.WEEKLY,
            template_id=template.id,
            business_date=biz_date,
            canteen_id=canteen_id,
            canteen_name_snapshot=canteen_name,
            status=InspectionTaskStatus.PENDING,
            form_snapshot=form_snapshot,
            tenant_id=current_user.tenant_id,
            executor_name_snapshot=current_user.real_name or current_user.username,
        )
        db.add(new_task)
        await db.flush()
        created_ids.append(new_task.id)

    await db.commit()
    return GenericResponse(
        code=20000,
        msg="下发成功",
        data={"created": created_ids, "skipped": skipped_ids},
    )


@router.get("/weekly-inspections/tasks", response_model=GenericResponse)
async def list_weekly_tasks(
    start_date: Optional[str] = Query(None, description="��ʼ���ڣ�YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="�������ڣ�YYYY-MM-DD"),
    status: Optional[str] = Query(None, description="����״̬"),
    keyword: Optional[str] = Query(None, description="�����ؼ��֣�ʳ��/�ύ��/ģ�壩"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    canteen_id: Optional[int] = Query(None, description="按食堂ID过滤"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, WEEKLY_VIEW, "无查看周排查任务权限")
    filters = [InspectionTask.inspection_type == InspectionType.WEEKLY]

    if start_date:
        filters.append(InspectionTask.business_date >= start_date)
    if end_date:
        filters.append(InspectionTask.business_date <= end_date)
    if status:
        filters.append(InspectionTask.status == status)
    if canteen_id:
        filters.append(InspectionTask.canteen_id == canteen_id)
    if keyword:
        pattern = f"%{keyword}%"
        filters.append(
            or_(
                InspectionTask.canteen_name_snapshot.ilike(pattern),
                InspectionTask.executor_name_snapshot.ilike(pattern),
            )
        )

    count_stmt = select(func.count()).where(*filters)
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        select(InspectionTask)
        .where(*filters)
        .options(selectinload(InspectionTask.template))  # Ԥ���ع�������
        .order_by(InspectionTask.business_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    tasks: List[InspectionTask] = result.scalars().all()

    items = []
    for task in tasks:
        status_value = task.status.value if hasattr(task.status, "value") else str(task.status)
        submission_date = None
        if task.submission_time is not None:
            submission_date = task.submission_time.date().isoformat()

        template_name = task.template.template_name if task.template is not None else None

        snap_max, snap_actual, snap_red, snap_yellow = _snapshot_stats(task.form_snapshot)
        # 优先用后端提交计算的 total_score，PENDING 任务则用快照预填分数
        display_score = task.total_score if task.total_score is not None else (snap_actual if snap_actual > 0 else None)

        items.append(
            {
                "id": task.id,
                "task_id": task.id,
                "canteen_id": task.canteen_id,
                "canteen_name": task.canteen_name_snapshot,
                "executor_name": task.executor_name_snapshot,
                "template_name": template_name,
                "total_score": display_score,
                "red_line_issues": task.red_line_issues,
                "submission_date": submission_date,
                "business_date": task.business_date.isoformat() if task.business_date else None,
                "status": status_value,
                "status_text": _status_text(status_value),
                # 从 form_snapshot 计算：满分总和、红线项数、黄线项数
                "max_score": snap_max,
                "red_line_count": snap_red,
                "yellow_line_count": snap_yellow,
            }
        )

    return GenericResponse(
        code=20000,
        msg="success",
        data={"total": total, "list": items},
    )


@router.get("/weekly-inspections/tasks/{task_id}", response_model=GenericResponse)
async def get_weekly_task_detail(
    task_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, WEEKLY_VIEW, "无查看周排查任务权限")
    stmt = select(InspectionTask).where(
        InspectionTask.id == task_id,
        InspectionTask.inspection_type == InspectionType.WEEKLY,
    )
    result = await db.execute(stmt)
    task: Optional[InspectionTask] = result.scalar_one_or_none()
    if not task:
        return GenericResponse(code=40400, msg="���񲻴���", data=None)

    status_value = task.status.value if hasattr(task.status, "value") else str(task.status)

    result_stmt = select(InspectionResult).where(InspectionResult.task_id == task_id)
    result_rows = await db.execute(result_stmt)
    result_list: List[InspectionResult] = result_rows.scalars().all()
    result_map = {str(result.item_id): result for result in result_list}

    form_snapshot = task.form_snapshot
    if isinstance(form_snapshot, dict):
        form_snapshot = dict(form_snapshot)
        form_snapshot["inspector_id"] = task.inspector_id
        major_items = form_snapshot.get("major_items")
        if isinstance(major_items, list):
            merged_major_items = []
            for major in major_items:
                major_data = dict(major)
                minor_items = major_data.get("minor_items")
                if isinstance(minor_items, list):
                    merged_minor_items = []
                    for minor in minor_items:
                        minor_data = dict(minor)
                        result = result_map.get(str(minor_data.get("item_id")))
                        if result:
                            minor_data["result_id"] = result.id
                            minor_data["score_given"] = result.score_given
                            minor_data["inspection_description"] = result.inspection_description
                            minor_data["inspection_photos"] = result.inspection_photos
                            minor_data["rectification_description"] = result.rectification_description
                            minor_data["rectification_photos"] = result.rectification_photos
                        merged_minor_items.append(minor_data)
                    major_data["minor_items"] = merged_minor_items
                merged_major_items.append(major_data)
            form_snapshot["major_items"] = merged_major_items

    task_info = {
        "task_id": task.id,
        "canteen_name": task.canteen_name_snapshot,
        "inspector_name": task.executor_name_snapshot,
        "actual_start_time": _to_utc_iso(task.actual_start_time),
        "submission_date": _to_utc_iso(task.submission_time),
        "business_date": task.business_date.isoformat() if task.business_date else None,
        "status": status_value,
        "status_text": _status_text(status_value),
        "total_score": task.total_score,
        "red_line_issues": task.red_line_issues,
    }

    return GenericResponse(
        code=20000,
        msg="success",
        data={
            "task_info": task_info,
            "form_snapshot": form_snapshot,
            "audit_logs": task.audit_logs or [],
        },
    )


@router.patch("/weekly-inspections/tasks/{task_id}/snapshot", response_model=GenericResponse)
async def update_weekly_task_snapshot(
    request: WeeklySnapshotUpdateRequest,
    task_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """监管端更新 PENDING 任务的预填快照（下发后仍可补充检查说明/照片/评分）。"""
    await _ensure_permission(db, current_user, WEEKLY_PUBLISH, "无下发周排查权限")

    task_result = await db.execute(
        select(InspectionTask).where(
            InspectionTask.id == task_id,
            InspectionTask.inspection_type == InspectionType.WEEKLY,
            InspectionTask.tenant_id == current_user.tenant_id,
        )
    )
    task: Optional[InspectionTask] = task_result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail={"code": 40400, "msg": "任务不存在", "data": None})
    if task.status != InspectionTaskStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail={"code": 40000, "msg": "只有待提交的任务才能更新预填快照", "data": None},
        )

    task.form_snapshot = request.form_snapshot
    await db.commit()
    return GenericResponse(code=20000, msg="预填信息已保存", data=None)


@router.delete("/weekly-inspections/tasks/{task_id}", response_model=GenericResponse)
async def delete_weekly_task(
    task_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """监管端删除（取消）周排查任务记录，软删除为 CANCELLED 状态。"""
    await _ensure_permission(db, current_user, WEEKLY_PUBLISH, "无操作权限")

    task_result = await db.execute(
        select(InspectionTask).where(
            InspectionTask.id == task_id,
            InspectionTask.inspection_type == InspectionType.WEEKLY,
            InspectionTask.tenant_id == current_user.tenant_id,
        )
    )
    task: Optional[InspectionTask] = task_result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail={"code": 40400, "msg": "任务不存在", "data": None})

    task.status = InspectionTaskStatus.CANCELLED
    await db.commit()
    return GenericResponse(code=20000, msg="记录已删除", data=None)


@router.post("/weekly-inspections/tasks/{task_id}/submit", response_model=GenericResponse)
async def submit_weekly_task(
    request: WeeklyInspectionSubmitRequest,
    task_id: int = Path(..., ge=1),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, WEEKLY_SUBMIT, "���ύȨ��")

    is_admin = current_user.username == "admin" and settings.environment != "production"
    if not is_admin:
        allowed_ids = {
            str(current_user.id),
            current_user.username,
            f"user-regulator-{current_user.username}",
        }
        if request.inspector_id not in allowed_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": 40300, "msg": "inspector_id与当前用户不匹配", "data": None},
            )

    inspector_name = current_user.real_name or current_user.username
    task = await InspectionService.submit_weekly_task(
        db,
        task_id,
        request,
        idempotency_key,
        inspector_name=inspector_name,
    )
    return GenericResponse(
        code=20000,
        msg="success",
        data={
            "task_id": task.id,
            "status": task.status.value if hasattr(task.status, "value") else str(task.status),
        },
    )


@router.post("/weekly-inspections/tasks/{task_id}/rectify", response_model=GenericResponse)
async def rectify_weekly_task(
    request: WeeklyRectifyRequest,
    task_id: int = Path(..., ge=1),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, WEEKLY_RECTIFY, "������Ȩ��")

    task = await InspectionService.rectify_weekly_task(db, task_id, request, idempotency_key)
    return GenericResponse(
        code=20000,
        msg="�����ύ�ɹ�",
        data={
            "task_id": task.id,
            "status": task.status.value if hasattr(task.status, "value") else str(task.status),
        },
    )

# ==========================================
# ����Ѳ�� (JOINT INSPECTION)
# ==========================================

@router.get("/joint-inspections/templates", response_model=GenericResponse)
async def list_joint_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, JOINT_VIEW, "�޲鿴����Ѳ��ģ��Ȩ��")
    result = await InspectionTemplateService.list_templates(
        db, InspectionType.JOINT, page, page_size
    )
    items = []
    for template in result["records"]:
        items.append({
            "id": template.id,
            "template_name": template.template_name,
            "executor_role": template.executor_role,
            "approver_role": template.approver_role,
            "form_type": template.form_type,
            "start_time": template.start_time,
            "end_time": template.end_time,
            "is_active": template.is_active,
            "target_node_ids": _raw_target_node_ids(template.target_node_ids_raw),
            "created_at": _to_utc_iso(template.created_at),
            "updated_at": _to_utc_iso(template.updated_at),
        })
    return GenericResponse(code=20000, msg="success", data={"total": result["total"], "list": items})

@router.post("/joint-inspections/templates", response_model=GenericResponse)
async def create_joint_template(
    request: WeeklyTemplateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, JOINT_CREATE_TEMPLATE, "�޴�������Ѳ��ģ��Ȩ��")
    template = await InspectionTemplateService.create_joint_template(
        db, current_user, request
    )
    return GenericResponse(code=20000, msg="success", data={"id": template.id})


@router.get("/joint-inspections/templates/{template_id}", response_model=GenericResponse)
async def get_joint_template(
    template_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, JOINT_VIEW, "�޲鿴����Ѳ��ģ��Ȩ��")
    template = await InspectionTemplateService.get_template(
        db, current_user.tenant_id, template_id, InspectionType.JOINT
    )

    groups = [i for i in template.items if i.item_type == ItemType.GROUP]
    children_map = {}
    for item in template.items:
        if item.parent_item_id:
            children_map.setdefault(item.parent_item_id, []).append(item)

    major_items = []
    for group in sorted(groups, key=lambda x: x.sort_order):
        minor_items = []
        for minor in sorted(children_map.get(group.id, []), key=lambda x: x.sort_order):
            minor_items.append(
                {
                    "item_id": minor.id,
                    "sort_order": minor.sort_order,
                    "content": minor.content,
                    "issue_type": minor.issue_type,
                    "total_score": minor.total_score,
                    "scoring_options": minor.scoring_options,
                    "is_active": minor.is_active,
                }
            )
        major_items.append(
            {
                "title": group.content,
                "sort_order": group.sort_order,
                "minor_items": minor_items,
            }
        )

    data = {
        "id": template.id,
        "template_name": template.template_name,
        "executor_role": template.executor_role,
        "approver_role": template.approver_role,
        "form_type": template.form_type,
        "start_time": template.start_time,
        "end_time": template.end_time,
        "target_node_ids": _raw_target_node_ids(template.target_node_ids_raw),
        "major_items": major_items,
        "is_active": template.is_active,
        "created_at": _to_utc_iso(template.created_at),
        "updated_at": _to_utc_iso(template.updated_at),
    }
    return GenericResponse(code=20000, msg="success", data=data)


@router.put("/joint-inspections/templates/{template_id}", response_model=GenericResponse)
async def update_joint_template(
    request: WeeklyTemplateRequest,
    template_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, JOINT_CREATE_TEMPLATE, "无编辑联合巡检模板权限")
    template = await InspectionTemplateService.update_joint_template(
        db, template_id, current_user, request
    )
    return GenericResponse(code=20000, msg="success", data={"id": template.id})


@router.patch("/joint-inspections/templates/{template_id}/status", response_model=GenericResponse)
async def update_joint_template_status(
    request: TemplateStatusRequest,
    template_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, JOINT_PUBLISH, "无发布联合巡检模板权限")
    template = await InspectionTemplateService.update_template_status(
        db, current_user.tenant_id, template_id, InspectionType.JOINT, request.is_active
    )
    return GenericResponse(
        code=20000,
        msg="success",
        data={"id": template.id, "is_active": template.is_active},
    )


@router.delete("/joint-inspections/templates/{template_id}", response_model=GenericResponse)
async def delete_joint_template(
    template_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, JOINT_CREATE_TEMPLATE, "��ɾ������Ѳ��ģ��Ȩ��")
    await InspectionTemplateService.delete_template(
        db, current_user.tenant_id, template_id, InspectionType.JOINT
    )
    return GenericResponse(code=20000, msg="success", data={"id": template_id})

@router.get("/joint-inspections/tasks", response_model=GenericResponse)
async def list_joint_tasks(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, JOINT_VIEW, "�޲鿴����Ѳ������Ȩ��")
    filters = [InspectionTask.inspection_type == InspectionType.JOINT]

    if start_date:
        filters.append(InspectionTask.business_date >= start_date)
    if end_date:
        filters.append(InspectionTask.business_date <= end_date)
    if status:
        filters.append(InspectionTask.status == status)
    if keyword:
        pattern = f"%{keyword}%"
        filters.append(
            or_(
                InspectionTask.canteen_name_snapshot.ilike(pattern),
                InspectionTask.executor_name_snapshot.ilike(pattern),
            )
        )

    count_stmt = select(func.count()).select_from(InspectionTask).where(*filters)
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        select(InspectionTask)
        .where(*filters)
        .options(selectinload(InspectionTask.template))
        .order_by(InspectionTask.business_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    tasks = (await db.execute(stmt)).scalars().all()

    items = []
    for task in tasks:
        status_value = task.status.value if hasattr(task.status, "value") else str(task.status)
        submission_date = task.submission_time.date().isoformat() if task.submission_time else None
        template_name = task.template.template_name if task.template else None

        items.append({
            "id": task.id,
            "canteen_name": task.canteen_name_snapshot,
            "template_name": template_name,
            "executor_name": task.executor_name_snapshot,
            "submission_date": submission_date,
            "status": status_value,
            "total_score": task.total_score,
            "red_line_issues": task.red_line_issues,
            "business_date": task.business_date.isoformat(),
        })
    return GenericResponse(code=20000, msg="success", data={"total": total, "list": items})


@router.get("/joint-inspections/tasks/{task_id}", response_model=GenericResponse)
async def get_joint_task_detail(
    task_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, JOINT_VIEW, "无查看联合巡检任务权限")

    stmt = select(InspectionTask).where(
        InspectionTask.id == task_id,
        InspectionTask.inspection_type == InspectionType.JOINT,
    )
    task = (await db.execute(stmt)).scalar_one_or_none()
    if not task:
        return GenericResponse(code=40400, msg="���񲻴���", data=None)

    status_value = task.status.value if hasattr(task.status, "value") else str(task.status)

    result_stmt = select(InspectionResult).where(InspectionResult.task_id == task_id)
    result_list = (await db.execute(result_stmt)).scalars().all()
    result_map = {str(result.item_id): result for result in result_list}

    form_snapshot = task.form_snapshot
    if isinstance(form_snapshot, dict):
        form_snapshot = dict(form_snapshot)
        form_snapshot["inspector_id"] = task.inspector_id
        major_items = form_snapshot.get("major_items")
        if isinstance(major_items, list):
            merged_major_items = []
            for major in major_items:
                major_data = dict(major)
                minor_items = major_data.get("minor_items")
                if isinstance(minor_items, list):
                    merged_minor_items = []
                    for minor in minor_items:
                        minor_data = dict(minor)
                        result = result_map.get(str(minor_data.get("item_id")))
                        if result:
                            minor_data["result_id"] = result.id
                            minor_data["score_given"] = result.score_given
                            minor_data["inspection_description"] = result.inspection_description
                            minor_data["inspection_photos"] = result.inspection_photos
                            minor_data["rectification_description"] = result.rectification_description
                            minor_data["rectification_photos"] = result.rectification_photos
                        merged_minor_items.append(minor_data)
                    major_data["minor_items"] = merged_minor_items
                merged_major_items.append(major_data)
            form_snapshot["major_items"] = merged_major_items

    task_info = {
        "task_id": task.id,
        "canteen_name": task.canteen_name_snapshot,
        "inspector_name": task.executor_name_snapshot,
        "inspector_id": task.inspector_id,
        "actual_start_time": _to_utc_iso(task.actual_start_time),
        "submission_date": _to_utc_iso(task.submission_time),
        "status": status_value,
        "status_text": _status_text(status_value),
        "total_score": task.total_score,
        "red_line_issues": task.red_line_issues,
        "joint_participant_ids": task.joint_participant_ids or [],
        "joint_signatures": task.joint_signatures or {},
    }

    return GenericResponse(
        code=20000,
        msg="success",
        data={
            "task_info": task_info,
            "form_snapshot": form_snapshot,
            "audit_logs": task.audit_logs or [],
        },
    )

@router.post("/joint-inspections/tasks/{task_id}/submit", response_model=GenericResponse)
async def submit_joint_task(
    request: WeeklyInspectionSubmitRequest,
    task_id: int = Path(..., ge=1),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, JOINT_SUBMIT, "���ύȨ��")
    task = await InspectionWorkflow.submit_task(
        db, task_id, request, idempotency_key, 
        InspectionType.JOINT, 
        inspector_name=current_user.real_name or current_user.username
    )
    return GenericResponse(code=20000, msg="success", data={"task_id": task.id, "status": task.status.value if hasattr(task.status, "value") else str(task.status)})

@router.post("/joint-inspections/tasks/{task_id}/rectify", response_model=GenericResponse)
async def rectify_joint_task(
    request: WeeklyRectifyRequest,
    task_id: int = Path(..., ge=1),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, JOINT_RECTIFY, "������Ȩ��")
    task = await InspectionWorkflow.rectify_task(
        db, task_id, request, idempotency_key, InspectionType.JOINT
    )
    return GenericResponse(code=20000, msg="整改提交成功", data={"task_id": task.id, "status": task.status.value if hasattr(task.status, "value") else str(task.status)})

@router.post("/joint-inspections/tasks/{task_id}/audit", response_model=GenericResponse)
async def audit_joint_task(
    request: AuditRequest,
    task_id: int = Path(..., ge=1),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, JOINT_APPROVE, "�����Ȩ��")
    task = await InspectionWorkflow.audit_task(
        db, task_id,
        auditor_id=request.auditor_id,
        action=request.action,
        audit_opinion=request.opinion,
        idempotency_key=idempotency_key,
        inspection_type=InspectionType.JOINT
    )
    return GenericResponse(code=20000, msg="success", data={"task_id": task.id, "status": task.status.value if hasattr(task.status, "value") else str(task.status)})

@router.post("/joint-inspections/tasks/{task_id}/sign", response_model=GenericResponse)
async def sign_joint_task(
    request: JointSignRequest,
    task_id: int = Path(..., ge=1),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, JOINT_SIGN, "��Эͬǩ��Ȩ��")
    task = await JointInspectionService.sign_task(
        db, task_id, request.participant_id, request.signature, idempotency_key
    )
    return GenericResponse(code=20000, msg="ǩ�ֳɹ�", data={"task_id": task.id})


# ==========================================
# �µ��ȱ��� (MONTHLY REPORT)
# ==========================================

@router.post("/monthly-reports/preview", response_model=GenericResponse)
async def preview_monthly_report(
    request: MonthlyReportPreviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, MONTHLY_VIEW_REPORT, "�޲鿴�µ��ȱ���Ȩ��")
    data = await MonthlyReportService.preview_aggregation(
        db, request.start_date, request.end_date, request.data_sources
    )
    return GenericResponse(code=20000, msg="success", data=data)

@router.post("/monthly-reports/export")
async def export_monthly_report(
    request: MonthlyReportExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, MONTHLY_DOWNLOAD_REPORT, "无导出月调度报告权限")
    file_bytes = await MonthlyReportService.generate_export(
        db, request.start_date, request.end_date, request.data_sources, request.export_format
    )
    return Response(
        content=file_bytes,
        media_type="application/pdf" if request.export_format == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="月调度报告.{request.export_format}"'}
    )

@router.get("/monthly-reports", response_model=GenericResponse)
async def list_monthly_reports(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    canteen_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, MONTHLY_VIEW_REPORT, "�޲鿴�µ��ȱ���Ȩ��")
    data = await MonthlyReportService.list_reports(
        db, start_date, end_date, canteen_id, page, page_size
    )
    return GenericResponse(code=20000, msg="success", data=data)

@router.post("/monthly-reports/offline-upload", response_model=GenericResponse)
async def upload_offline_monthly_report(
    request: MonthlyReportUploadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, MONTHLY_UPLOAD_REPORT, "无上传月调度报告权限")
    if request.file_key:
        file_url = request.file_key
    else:
        file_url = f"https://mock.oss/{request.canteen_id}/report.pdf"
    report = await MonthlyReportService.save_offline_report(
        db,
        title=request.title,
        canteen_id=request.canteen_id,
        canteen_name=f"食堂{request.canteen_id}",
        reporter_id=str(current_user.id),
        reporter_name=current_user.real_name or current_user.username,
        file_url=file_url,
        remark=request.remark,
        tenant_id=current_user.tenant_id
    )
    return GenericResponse(code=20000, msg="success", data={"id": report.id, "file_url": file_url})


@router.post("/monthly-reports/offline-files/upload", response_model=GenericResponse)
async def upload_monthly_report_file(
    request: Request,
    canteen_id: int = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, MONTHLY_UPLOAD_REPORT, "无上传月调度报告权限")

    ext = os.path.splitext(file.filename or "")[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": 40000, "msg": f"不支持的文件类型，仅支持：{', '.join(ALLOWED_EXTENSIONS)}", "data": None}
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": 40000, "msg": "文件大小超过50MB限制", "data": None}
        )

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    safe_filename = f"{timestamp}_{current_user.id}_{canteen_id}{ext}"
    filepath = os.path.join(_MONTHLY_REPORT_FILE_DIR, safe_filename)

    with open(filepath, "wb") as f:
        f.write(content)

    base_url = _get_base_url(request)
    file_key = safe_filename
    file_url = f"{base_url}/files/monthly-reports/{file_key}"
    public_url, expires_at = _build_signed_public_url(base_url, file_key, 3600 * 24 * 7)

    return GenericResponse(code=20000, msg="success", data={
        "file_key": file_key,
        "file_url": file_url,
        "public_url": public_url,
        "expires_at": datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat()
    })


@router.delete("/monthly-reports/{report_id}", response_model=GenericResponse)
async def delete_monthly_report(
    report_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, MONTHLY_DELETE_REPORT, "无删除月调度报告权限")
    success = await MonthlyReportService.delete_report(
        db, report_id, current_user.tenant_id
    )
    if not success:
        return GenericResponse(code=40400, msg="报告不存在或已删除", data=None)
    return GenericResponse(code=20000, msg="删除成功", data={"id": report_id})


@router.get("/files/monthly-reports/{file_key}")
async def get_monthly_report_file(
    file_key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filepath = os.path.join(_MONTHLY_REPORT_FILE_DIR, file_key)
    if not os.path.exists(filepath):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": 40400, "msg": "文件不存在", "data": None}
        )
    return FileResponse(filepath)


@router.get("/files/monthly-reports/public/{token}")
async def get_public_monthly_report_file(
    token: str,
):
    file_key, expires_at = _decode_public_file_token(token)
    filepath = os.path.join(_MONTHLY_REPORT_FILE_DIR, file_key)
    if not os.path.exists(filepath):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": 40400, "msg": "文件不存在", "data": None}
        )
    return FileResponse(filepath)


@router.delete("/monthly-reports/{report_id}", response_model=GenericResponse)
async def delete_monthly_report(
    report_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, MONTHLY_VIEW_REPORT, "��ɾ���µ��ȱ���Ȩ��")
    stmt = select(MonthlyReport).where(
        MonthlyReport.id == report_id,
        MonthlyReport.is_deleted == False,
    )
    result = await db.execute(stmt)
    report: Optional[MonthlyReport] = result.scalar_one_or_none()
    if not report:
        return GenericResponse(code=40400, msg="���治����", data=None)
    report.is_deleted = True
    await db.commit()
    return GenericResponse(code=20000, msg="success", data=None)


@router.post("/weekly-inspections/tasks/{task_id}/audit", response_model=GenericResponse)
async def audit_weekly_task(
    request: AuditRequest,
    task_id: int = Path(..., ge=1),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, WEEKLY_APPROVE_RECTIFY, "无审核权限")

    # Apply per-item scores before audit if provided
    if request.item_scores:
        score_map = {entry.result_id: entry.score for entry in request.item_scores}
        result_rows = (
            await db.execute(
                select(InspectionResult).where(
                    InspectionResult.task_id == task_id,
                    InspectionResult.id.in_(list(score_map.keys())),
                )
            )
        ).scalars().all()
        new_total = 0.0
        for result in result_rows:
            result.score_given = score_map[result.id]
            new_total += score_map[result.id]
        # Update task total_score
        task_obj = await db.get(InspectionTask, task_id)
        if task_obj:
            task_obj.total_score = new_total
        await db.flush()

    task = await InspectionService.audit_weekly_task(
        db,
        task_id,
        auditor_id=request.auditor_id,
        action=request.action,
        audit_opinion=request.opinion,
        idempotency_key=idempotency_key,
    )
    return GenericResponse(
        code=20000,
        msg="��˳ɹ�" if request.action == "PASS" else "�Ѳ���",
        data={
            "task_id": task.id,
            "status": task.status.value if hasattr(task.status, "value") else str(task.status),
        },
    )


@router.post("/daily-controls/tasks/{task_id}/submit", response_model=GenericResponse)
async def submit_daily_task(
    request: DailyControlSubmitRequest,
    task_id: int = Path(..., ge=1),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """�չܿ�ʳ�ö��ύ�Բ�"""
    await _ensure_permission(db, current_user, DAILY_SUBMIT, "���ύȨ��")
    task = await InspectionService.submit_daily_task(db, task_id, request, idempotency_key)
    return GenericResponse(
        code=20000,
        msg="success",
        data={
            "task_id": task.id,
            "status": task.status.value if hasattr(task.status, "value") else str(task.status),
        },
    )



@router.post("/daily-controls/tasks/{task_id}/audit", response_model=GenericResponse)
async def audit_daily_task(
    request: AuditRequest,
    task_id: int = Path(..., ge=1),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """�չܿؼ�ܶ����"""
    await _ensure_permission(db, current_user, DAILY_APPROVE, "�����Ȩ��")
    task = await InspectionService.audit_daily_task(
        db,
        task_id,
        auditor_id=request.auditor_id,
        action=request.action,
        audit_opinion=request.opinion,
        idempotency_key=idempotency_key,
    )
    return GenericResponse(
        code=20000,
        msg="��˳ɹ�" if request.action == "PASS" else "�Ѳ���",
        data={
            "task_id": task.id,
            "status": task.status.value if hasattr(task.status, "value") else str(task.status),
        },
    )


@router.post("/daily-controls/tasks/{task_id}/rectify", response_model=GenericResponse)
async def rectify_daily_task(
    request: DailyRectifyRequest,
    task_id: int = Path(..., ge=1),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """�չܿ�ʳ�ö��ύ����"""
    await _ensure_permission(db, current_user, DAILY_SUBMIT, "������Ȩ��")
    task = await InspectionService.rectify_daily_task(db, task_id, request, idempotency_key)
    return GenericResponse(
        code=20000,
        msg="�����ύ�ɹ�",
        data={
            "task_id": task.id,
            "status": task.status.value if hasattr(task.status, "value") else str(task.status),
        },
    )
