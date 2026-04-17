import base64
import binascii
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.modules.video.models import BizVideoCamera

from app.core.constants.permissions import (
    DEVICE_EDIT,
    VIDEO_APPROVE_RECTIFY,
    VIDEO_CREATE_TEMPLATE,
    VIDEO_INSPECT,
    VIDEO_SNAPSHOT,
    VIDEO_RECTIFY,
    VIDEO_VIEW_RECORD,
    VIDEO_WATCH,
    VIDEO_WATCH_ALL,
)
from app.core.context import UserContext
from app.core.deps import get_current_user
from app.db.session import get_db
from app.modules.inspection.models import (
    InspectionItem,
    InspectionResult,
    InspectionTask,
    InspectionTemplate,
    InspectionType,
    ItemType,
)
from app.modules.inspection.schemas import (
    TemplateStatusRequest,
    VideoTemplateRequest,
    WeeklyInspectionSubmitRequest,
    WeeklyRectifyRequest,
)
from app.modules.inspection.service import InspectionService, InspectionTemplateService
from app.modules.user.models import Org as OrgModel, User
from app.modules.user.service import get_permissions_for_user
from app.modules.video.schemas import (
    HikvisionChannelSyncRequest,
    HikvisionEncryptOffRequest,
    HikvisionPlayParamsRequest,
    VideoCaptureRequest,
)
from app.modules.video.service import HikvisionAuthService, HikvisionOpenApiService

router = APIRouter()
logger = logging.getLogger(__name__)


class GenericResponse(BaseModel):
    code: int
    msg: str
    request_id: Optional[str] = None
    data: Optional[dict] = None


class AuditRequest(BaseModel):
    auditor_id: str
    action: str = Field(..., pattern="^(PASS|REJECT)$")
    opinion: Optional[str] = None


def _to_utc_iso(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.isoformat().replace("+00:00", "Z")


def _to_uikit_datetime(value: str) -> str:
    text = value.strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.strftime("%Y%m%d%H%M%S")


def _status_text(status_value: str) -> str:
    mapping = {
        "PENDING": "Pending",
        "SUBMITTED": "Submitted",
        "REJECTED": "Rejected",
        "RECTIFIED": "Rectified",
        "COMPLETED": "Completed",
    }
    return mapping.get(status_value, status_value)


def _raw_target_node_ids(value: Optional[dict]) -> List[int]:
    if isinstance(value, dict):
        raw = value.get("raw")
        if isinstance(raw, list):
            return [item for item in raw if isinstance(item, int)]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, int)]
    return []


def _org_node(org: OrgModel) -> dict:
    return {
        "id": org.id,
        "name": org.name,
        "type": org.org_type,
        "parentId": org.parent_id,
        "children": [],
    }


def _build_org_tree(orgs: List[OrgModel]) -> Tuple[List[dict], Dict[int, dict]]:
    nodes = {org.id: _org_node(org) for org in orgs}
    roots = []
    for org in orgs:
        node = nodes[org.id]
        parent_id = org.parent_id
        if parent_id and parent_id in nodes:
            nodes[parent_id]["children"].append(node)
        else:
            roots.append(node)
    return roots, nodes


def _safe_filename_part(raw: str) -> str:
    text = re.sub(r"[^0-9A-Za-z._-]", "_", raw)
    return text[:64] or "camera"


def _resolve_image_extension(data_prefix: str) -> str:
    lowered = data_prefix.lower()
    if "image/png" in lowered:
        return "png"
    if "image/webp" in lowered:
        return "webp"
    if "image/jpg" in lowered or "image/jpeg" in lowered:
        return "jpg"
    return "jpg"


def _extract_base64_payload(image_base64: str) -> Tuple[str, str]:
    value = image_base64.strip()
    if not value:
        raise ValueError("image_base64 is empty")
    if value.startswith("data:"):
        prefix, sep, payload = value.partition(",")
        if not sep:
            raise ValueError("invalid data url")
        return prefix, payload.strip()
    return "", value


def _collect_descendant_canteen_ids(orgs: List[OrgModel], root_id: int) -> List[int]:
    children_map: Dict[Optional[int], List[OrgModel]] = {}
    for org in orgs:
        children_map.setdefault(org.parent_id, []).append(org)

    result: List[int] = []
    queue: List[int] = [root_id]
    while queue:
        current = queue.pop(0)
        for child in children_map.get(current, []):
            if child.org_type == "CANTEEN":
                result.append(child.id)
            queue.append(child.id)
    return sorted(set(result))


def _collect_visible_org_ids(orgs: List[OrgModel], canteen_ids: List[int]) -> set[int]:
    if not canteen_ids:
        return set()
    parent_map = {org.id: org.parent_id for org in orgs}
    visible_ids: set[int] = set()
    for canteen_id in canteen_ids:
        current = canteen_id
        while current is not None and current not in visible_ids:
            visible_ids.add(current)
            current = parent_map.get(current)
    return visible_ids


def _filter_tree_by_visible_ids(nodes: List[dict], visible_org_ids: set[int]) -> List[dict]:
    filtered: List[dict] = []
    for node in nodes:
        if node.get("type") == "CAMERA":
            filtered.append(node)
            continue
        node_id = node.get("id")
        if node_id not in visible_org_ids:
            continue
        current = dict(node)
        current["children"] = _filter_tree_by_visible_ids(node.get("children", []), visible_org_ids)
        filtered.append(current)
    return filtered


async def _ensure_permission(
    db: AsyncSession,
    user: User,
    permission: str,
    msg: str,
) -> None:
    permissions = await get_permissions_for_user(db, user)
    if permission not in permissions:
        logger.warning(
            "video_permission_denied uid=%s tenant_id=%s required_permission=%s actual_permissions=%s app_client=%s",
            user.id,
            user.tenant_id,
            permission,
            sorted(list(permissions)),
            UserContext.get_app_client(),
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": 40300, "msg": msg, "data": None},
        )


@router.get("/video/cameras/tree", response_model=GenericResponse)
async def get_video_camera_tree(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    permissions = set(await get_permissions_for_user(db, current_user))
    has_watch = VIDEO_WATCH in permissions
    has_watch_all = VIDEO_WATCH_ALL in permissions
    if not has_watch and not has_watch_all:
        logger.warning(
            "video_permission_denied uid=%s tenant_id=%s required_permission=%s actual_permissions=%s app_client=%s",
            current_user.id,
            current_user.tenant_id,
            f"{VIDEO_WATCH}|{VIDEO_WATCH_ALL}",
            sorted(list(permissions)),
            UserContext.get_app_client(),
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": 40300, "msg": "No permission to view cameras", "data": None},
        )

    orgs = (
        await db.execute(select(OrgModel).where(OrgModel.tenant_id == current_user.tenant_id))
    ).scalars().all()
    org_list = list(orgs)
    org_by_id = {org.id: org for org in org_list}

    allowed_canteen_ids: List[int] = []
    if not has_watch_all:
        user_org_id = current_user.org_id
        if user_org_id is None:
            return GenericResponse(code=20000, msg="success", data={"tree": []})
        user_org = org_by_id.get(user_org_id)
        if user_org is None:
            return GenericResponse(code=20000, msg="success", data={"tree": []})
        if user_org.org_type == "CANTEEN":
            allowed_canteen_ids = [user_org.id]
        else:
            allowed_canteen_ids = _collect_descendant_canteen_ids(org_list, user_org.id)
        if not allowed_canteen_ids:
            return GenericResponse(code=20000, msg="success", data={"tree": []})

    roots, node_map = _build_org_tree(list(orgs))

    cameras_stmt = select(BizVideoCamera).where(
        BizVideoCamera.tenant_id == current_user.tenant_id,
        BizVideoCamera.is_active.is_(True),
    )
    if not has_watch_all:
        cameras_stmt = cameras_stmt.where(BizVideoCamera.canteen_id.in_(allowed_canteen_ids))

    cameras = (
        await db.execute(cameras_stmt)
    ).scalars().all()

    for camera in cameras:
        if not camera.canteen_id:
            continue
        parent = node_map.get(camera.canteen_id)
        if not parent:
            continue
        parent["children"].append(
            {
                "id": camera.camera_id,
                "cameraId": camera.camera_id,
                "name": camera.channel_name or camera.camera_id,
                "type": "CAMERA",
                "parentId": camera.canteen_id,
            }
        )

    tree_data = roots
    if not has_watch_all:
        visible_org_ids = _collect_visible_org_ids(org_list, allowed_canteen_ids)
        tree_data = _filter_tree_by_visible_ids(roots, visible_org_ids)
    return GenericResponse(code=20000, msg="success", data={"tree": tree_data})


@router.get("/video-inspections/templates", response_model=GenericResponse)
async def list_video_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, VIDEO_CREATE_TEMPLATE, "No permission to view video templates")
    result = await InspectionTemplateService.list_templates(
        db, current_user.tenant_id, InspectionType.VIDEO, page, page_size
    )
    items = []
    for template in result["records"]:
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
            }
        )
    return GenericResponse(
        code=20000,
        msg="success",
        data={"total": result["total"], "list": items},
    )


@router.post("/video-inspections/templates", response_model=GenericResponse)
async def create_video_template(
    request: VideoTemplateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, VIDEO_CREATE_TEMPLATE, "No permission to create video templates")
    template = await InspectionTemplateService.create_video_template(
        db, current_user, request
    )
    return GenericResponse(code=20000, msg="success", data={"id": template.id})


@router.get("/video-inspections/templates/{template_id}", response_model=GenericResponse)
async def get_video_template(
    template_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, VIDEO_CREATE_TEMPLATE, "No permission to view video templates")
    template = await InspectionTemplateService.get_template(
        db, current_user.tenant_id, template_id, InspectionType.VIDEO
    )
    groups = [item for item in template.items if item.item_type == ItemType.GROUP]
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
                    "associated_camera_ids": minor.associated_camera_ids or [],
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


@router.put("/video-inspections/templates/{template_id}", response_model=GenericResponse)
async def update_video_template(
    request: VideoTemplateRequest,
    template_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, VIDEO_CREATE_TEMPLATE, "No permission to edit video templates")
    template = await InspectionTemplateService.update_video_template(
        db, template_id, current_user, request
    )
    return GenericResponse(code=20000, msg="success", data={"id": template.id})


@router.patch("/video-inspections/templates/{template_id}/status", response_model=GenericResponse)
async def update_video_template_status(
    request: TemplateStatusRequest,
    template_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, VIDEO_CREATE_TEMPLATE, "No permission to publish video templates")
    template = await InspectionTemplateService.update_template_status(
        db, current_user.tenant_id, template_id, InspectionType.VIDEO, request.is_active
    )
    return GenericResponse(
        code=20000,
        msg="success",
        data={"id": template.id, "is_active": template.is_active},
    )


@router.delete("/video-inspections/templates/{template_id}", response_model=GenericResponse)
async def delete_video_template(
    template_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, VIDEO_CREATE_TEMPLATE, "No permission to delete video templates")
    await InspectionTemplateService.delete_template(
        db, current_user.tenant_id, template_id, InspectionType.VIDEO
    )
    return GenericResponse(code=20000, msg="success", data={"id": template_id})


@router.get("/video-inspections/tasks", response_model=GenericResponse)
async def list_video_tasks(
    start_date: Optional[str] = Query(None, description="Start date, YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date, YYYY-MM-DD"),
    status: Optional[str] = Query(None, description="Task status"),
    keyword: Optional[str] = Query(None, description="Search keyword"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, VIDEO_VIEW_RECORD, "No permission to view video tasks")
    filters = [InspectionTask.inspection_type == InspectionType.VIDEO]

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

    count_stmt = select(func.count()).where(*filters)
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
        items.append(
            {
                "task_id": task.id,
                "canteen_name": task.canteen_name_snapshot,
                "submitter_name": task.executor_name_snapshot,
                "template_name": template_name,
                "total_score": task.total_score,
                "red_line_issues": task.red_line_issues,
                "submission_date": submission_date,
                "status": status_value,
                "status_text": _status_text(status_value),
            }
        )

    return GenericResponse(code=20000, msg="success", data={"total": total, "list": items})


@router.get("/video-inspections/tasks/{task_id}", response_model=GenericResponse)
async def get_video_task_detail(
    task_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, VIDEO_VIEW_RECORD, "No permission to view video tasks")

    stmt = select(InspectionTask).where(
        InspectionTask.id == task_id,
        InspectionTask.inspection_type == InspectionType.VIDEO,
    )
    task = (await db.execute(stmt)).scalar_one_or_none()
    if not task:
        return GenericResponse(code=40400, msg="task not found", data=None)

    status_value = task.status.value if hasattr(task.status, "value") else str(task.status)

    result_stmt = select(InspectionResult).where(InspectionResult.task_id == task_id)
    result_list = (await db.execute(result_stmt)).scalars().all()
    result_map = {result.item_id: result for result in result_list}

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
                        result = result_map.get(minor_data.get("item_id"))
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


@router.post("/video-inspections/tasks/{task_id}/submit", response_model=GenericResponse)
async def submit_video_task(
    request: WeeklyInspectionSubmitRequest,
    task_id: int = Path(..., ge=1),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, VIDEO_INSPECT, "No permission to submit")

    allowed_ids = {
        str(current_user.id),
        current_user.username,
        f"user-regulator-{current_user.username}",
    }
    if request.inspector_id not in allowed_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": 40300, "msg": "inspector_id does not match current user", "data": None},
        )

    inspector_name = current_user.real_name or current_user.username
    task = await InspectionService.submit_video_task(
        db,
        task_id,
        request,
        idempotency_key,
        inspector_name=inspector_name,
    )
    return GenericResponse(
        code=20000,
        msg="success",
        data={"task_id": task.id, "status": task.status.value},
    )


@router.post("/video-inspections/tasks/{task_id}/rectify", response_model=GenericResponse)
async def rectify_video_task(
    request: WeeklyRectifyRequest,
    task_id: int = Path(..., ge=1),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, VIDEO_RECTIFY, "No permission to rectify")

    task = await InspectionService.rectify_video_task(db, task_id, request, idempotency_key)
    return GenericResponse(
        code=20000,
        msg="rectify submitted",
        data={"task_id": task.id, "status": task.status.value},
    )


@router.post("/video-inspections/tasks/{task_id}/audit", response_model=GenericResponse)
async def audit_video_task(
    request: AuditRequest,
    task_id: int = Path(..., ge=1),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, VIDEO_APPROVE_RECTIFY, "No permission to audit")

    task = await InspectionService.audit_video_task(
        db,
        task_id,
        auditor_id=request.auditor_id,
        action=request.action,
        audit_opinion=request.opinion,
        idempotency_key=idempotency_key,
    )
    return GenericResponse(
        code=20000,
        msg="audit passed" if request.action == "PASS" else "audit rejected",
        data={"task_id": task.id, "status": task.status.value},
    )


@router.post("/api/v1/video/hikvision/channels/sync", response_model=GenericResponse)
async def sync_hikvision_channels(
    request: HikvisionChannelSyncRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, DEVICE_EDIT, "No permission to sync channels")
    result = await HikvisionOpenApiService.sync_channels(
        db,
        current_user.tenant_id,
        request.device_serial,
        request.page_size,
    )
    return GenericResponse(code=20000, msg="success", data=result)


@router.post("/api/v1/video/hikvision/devices/encrypt/off", response_model=GenericResponse)
async def disable_hikvision_encrypt(
    request: HikvisionEncryptOffRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, DEVICE_EDIT, "No permission to disable encryption")
    result = await HikvisionOpenApiService.disable_encrypt(
        db,
        current_user.tenant_id,
        request.device_serial,
        request.validate_code,
    )
    return GenericResponse(code=20000, msg="success", data=result)


@router.post("/api/v1/video/hikvision/play-params", response_model=GenericResponse)
async def get_hikvision_play_params(
    request: HikvisionPlayParamsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, VIDEO_VIEW_RECORD, "No permission to view video")
    stmt = select(BizVideoCamera).where(
        BizVideoCamera.tenant_id == current_user.tenant_id,
        BizVideoCamera.camera_id == request.camera_id,
    )
    camera = (await db.execute(stmt)).scalar_one_or_none()
    if not camera:
        return GenericResponse(code=40400, msg="camera not found", data=None)

    action = request.action
    begin_value: Optional[str] = None
    end_value: Optional[str] = None
    if action == "playback":
        if not request.begin or not request.end:
            return GenericResponse(code=40000, msg="begin/end required for playback", data=None)
        try:
            begin_value = _to_uikit_datetime(request.begin)
            end_value = _to_uikit_datetime(request.end)
        except ValueError:
            return GenericResponse(code=40000, msg="invalid begin/end format", data=None)

    app_client = UserContext.get_app_client() or ""
    is_app = app_client.endswith("_app")

    if not is_app and camera.encrypt_enabled:
        return GenericResponse(
            code=40000,
            msg="device encrypted: please disable encryption or provide validate code",
            data=None,
        )
    if is_app and camera.encrypt_enabled and not camera.valid_code:
        return GenericResponse(
            code=40000,
            msg="device encrypted: please disable encryption or provide validate code",
            data=None,
        )

    if is_app:
        oauth_token = await HikvisionAuthService.get_access_token()
        payload = {
            "oauthToken": oauth_token,
            "deviceSerial": camera.device_serial,
            "channelNo": camera.channel_no,
        }
        if camera.encrypt_enabled and camera.valid_code:
            payload["validCode"] = camera.valid_code
        return GenericResponse(code=20000, msg="success", data=payload)

    stream_auth = await HikvisionOpenApiService.get_stream_auth_info()
    payload = {
        "uikitAccessToken": stream_auth["token"],
        "deviceSerial": camera.device_serial,
        "channelNo": camera.channel_no,
    }
    if begin_value and end_value:
        payload["begin"] = begin_value
        payload["end"] = end_value
    return GenericResponse(code=20000, msg="success", data=payload)


@router.post("/video-inspections/cameras/{camera_id}/capture", response_model=GenericResponse)
async def capture_video_frame(
    request: VideoCaptureRequest,
    camera_id: str = Path(..., min_length=1, max_length=64),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, VIDEO_SNAPSHOT, "No permission to capture snapshot")

    camera_stmt = select(BizVideoCamera).where(
        BizVideoCamera.tenant_id == current_user.tenant_id,
        BizVideoCamera.camera_id == camera_id,
        BizVideoCamera.is_active.is_(True),
    )
    camera = (await db.execute(camera_stmt)).scalar_one_or_none()
    if not camera:
        return GenericResponse(code=40400, msg="camera not found", data=None)

    try:
        prefix, payload = _extract_base64_payload(request.image_base64)
        binary = base64.b64decode(payload, validate=True)
    except (ValueError, binascii.Error):
        return GenericResponse(code=40000, msg="invalid image_base64", data=None)

    if not binary:
        return GenericResponse(code=40000, msg="empty image payload", data=None)

    image_dir = settings.image_upload_dir
    os.makedirs(image_dir, exist_ok=True)

    ext = _resolve_image_extension(prefix)
    safe_camera_id = _safe_filename_part(camera_id)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    file_name = f"capture_{safe_camera_id}_{ts}_{uuid.uuid4().hex[:8]}.{ext}"
    file_path = os.path.join(image_dir, file_name)

    with open(file_path, "wb") as fp:
        fp.write(binary)

    normalized_dir = image_dir.replace("\\", "/").strip("/")
    photo_url = f"/{normalized_dir}/{file_name}"
    return GenericResponse(code=20000, msg="success", data={"photo_url": photo_url})


@router.get("/video/scores/statistics", response_model=GenericResponse)
async def get_video_score_statistics(
    start_date: Optional[str] = Query(None, description="Start date, YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date, YYYY-MM-DD"),
    org_id: Optional[int] = Query(None, ge=1),
    canteen_id: Optional[int] = Query(None, ge=1),
    template_id: Optional[int] = Query(None, ge=1),
    keyword: Optional[str] = Query(None, description="Search keyword"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_permission(db, current_user, VIDEO_VIEW_RECORD, "No permission to view video score statistics")

    filters = [
        InspectionTask.tenant_id == current_user.tenant_id,
        InspectionTask.inspection_type == InspectionType.VIDEO,
    ]
    if start_date:
        filters.append(InspectionTask.business_date >= start_date)
    if end_date:
        filters.append(InspectionTask.business_date <= end_date)
    if canteen_id:
        filters.append(InspectionTask.canteen_id == canteen_id)
    if template_id:
        filters.append(InspectionTask.template_id == template_id)
    if keyword:
        pattern = f"%{keyword}%"
        filters.append(
            or_(
                InspectionTask.canteen_name_snapshot.ilike(pattern),
                InspectionTask.executor_name_snapshot.ilike(pattern),
            )
        )
    if org_id and not canteen_id:
        orgs = (
            await db.execute(select(OrgModel).where(OrgModel.tenant_id == current_user.tenant_id))
        ).scalars().all()
        org_map = {org.id: org for org in orgs}
        selected = org_map.get(org_id)
        if not selected:
            return GenericResponse(code=20000, msg="success", data={"total": 0, "list": []})
        if selected.org_type == "CANTEEN":
            filters.append(InspectionTask.canteen_id == selected.id)
        else:
            canteen_ids = _collect_descendant_canteen_ids(list(orgs), selected.id)
            if not canteen_ids:
                return GenericResponse(code=20000, msg="success", data={"total": 0, "list": []})
            filters.append(InspectionTask.canteen_id.in_(canteen_ids))

    yellow_expr = func.coalesce(
        func.sum(
            case(
                (
                    (InspectionResult.has_issue.is_(True))
                    & (InspectionItem.issue_type == "YELLOW_LINE"),
                    1,
                ),
                else_=0,
            )
        ),
        0,
    )

    base_stmt = (
        select(
            InspectionTask.id.label("task_id"),
            InspectionTask.canteen_id,
            InspectionTask.canteen_name_snapshot,
            InspectionTask.template_id,
            InspectionTask.status,
            InspectionTask.total_score,
            InspectionTask.red_line_issues,
            InspectionTask.submission_time,
            InspectionTask.business_date,
            InspectionTemplate.template_name,
            yellow_expr.label("yellow_line_issues"),
        )
        .select_from(InspectionTask)
        .join(InspectionTemplate, InspectionTemplate.id == InspectionTask.template_id)
        .outerjoin(InspectionResult, InspectionResult.task_id == InspectionTask.id)
        .outerjoin(InspectionItem, InspectionItem.id == InspectionResult.item_id)
        .where(*filters)
        .group_by(
            InspectionTask.id,
            InspectionTask.canteen_id,
            InspectionTask.canteen_name_snapshot,
            InspectionTask.template_id,
            InspectionTask.status,
            InspectionTask.total_score,
            InspectionTask.red_line_issues,
            InspectionTask.submission_time,
            InspectionTask.business_date,
            InspectionTemplate.template_name,
        )
    )

    total = len((await db.execute(base_stmt)).all())
    rows = (
        await db.execute(
            base_stmt
            .order_by(InspectionTask.business_date.desc(), InspectionTask.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()

    items = []
    for row in rows:
        status_value = row.status.value if hasattr(row.status, "value") else str(row.status)
        submission_date = row.submission_time.date().isoformat() if row.submission_time else None
        items.append(
            {
                "canteen_id": row.canteen_id,
                "canteen_name": row.canteen_name_snapshot,
                "template_id": row.template_id,
                "template_name": row.template_name,
                "total_score": row.total_score,
                "red_line_issues": row.red_line_issues,
                "yellow_line_issues": int(row.yellow_line_issues or 0),
                "status": status_value,
                "status_text": _status_text(status_value),
                "submission_date": submission_date,
            }
        )

    return GenericResponse(code=20000, msg="success", data={"total": total, "list": items})
