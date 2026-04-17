from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Any

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, selectinload

from app.core.enums import InspectionTaskStatus
from app.modules.inspection.models import (
    InspectionItem,
    InspectionResult,
    InspectionTask,
    InspectionTemplate,
    InspectionType,
    ItemType,
    IssueType,
)
from app.modules.inspection.schemas import (
    DailyControlSubmitRequest,
    DailyRectifyRequest,
    DailyTemplateRequest,
    VideoTemplateRequest,
    WeeklyInspectionSubmitRequest,
    WeeklyRectifyRequest,
    WeeklyTemplateRequest,
)
from app.modules.inspection.state_machine import validate_state_transition
from app.modules.user.models import Org as OrgModel


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _utc_iso(value: datetime) -> str:
    return _ensure_utc(value).isoformat().replace("+00:00", "Z")


def _raise_http_error(status_code: int, code: int, msg: str) -> None:
    raise HTTPException(
        status_code=status_code,
        detail={"code": code, "msg": msg, "data": None},
    )


class InspectionService:
    @staticmethod
    async def get_task_by_id(db: AsyncSession, task_id: int) -> Optional[InspectionTask]:
        result = await db.execute(
            select(InspectionTask).where(InspectionTask.id == task_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    def get_task_by_id_sync(db: Session, task_id: int) -> Optional[InspectionTask]:
        return db.query(InspectionTask).filter(InspectionTask.id == task_id).first()

    @staticmethod
    async def submit_daily_task(
        db: AsyncSession,
        task_id: int,
        request: DailyControlSubmitRequest,
        idempotency_key: str,
    ) -> InspectionTask:
        task = await InspectionService.get_task_by_id(db, task_id)
        if not task:
            _raise_http_error(
                status.HTTP_404_NOT_FOUND,
                40400,
                f"巡检任务 {task_id} 不存在",
            )

        if task.inspection_type != InspectionType.DAILY:
            _raise_http_error(
                status.HTTP_400_BAD_REQUEST,
                40000,
                f"任务 {task_id} 不是日管控任务",
            )

        if (
            task.last_idempotency_key == idempotency_key
            and task.last_idempotency_action == "DAILY_SUBMIT"
        ):
            return task

        validate_state_transition(
            current_state=task.status,
            target_state=InspectionTaskStatus.SUBMITTED
        )

        task.status = InspectionTaskStatus.SUBMITTED
        task.submission_time = _utc_now()
        task.executor_id = request.submitter_id
        task.actual_start_time = _ensure_utc(request.actual_start_time)

        task.total_items = len(request.results)
        task.finished_items = len(request.results)

        await db.execute(
            delete(InspectionResult).where(InspectionResult.task_id == task.id)
        )

        for item_data in request.results:
            result = InspectionResult(
                task_id=task.id,
                item_id=item_data.item_id,
                inspection_type=InspectionType.DAILY,
                is_qualified=item_data.is_qualified,
                inspection_description=item_data.description,
                inspection_photos=item_data.photos,
            )
            db.add(result)

        task.last_idempotency_key = idempotency_key
        task.last_idempotency_action = "DAILY_SUBMIT"

        await db.commit()
        await db.refresh(task)
        return task


    @staticmethod
    async def submit_task(db: AsyncSession, task_id: int) -> InspectionTask:
        task = await InspectionService.get_task_by_id(db, task_id)
        if not task:
            _raise_http_error(
                status.HTTP_404_NOT_FOUND,
                40400,
                f"巡检任务 {task_id} 不存在",
            )

        validate_state_transition(
            current_state=task.status,
            target_state=InspectionTaskStatus.SUBMITTED
        )

        task.status = InspectionTaskStatus.SUBMITTED
        task.submission_time = _utc_now()
        await db.commit()
        await db.refresh(task)
        return task

    @staticmethod
    async def audit_daily_task(
        db: AsyncSession,
        task_id: int,
        auditor_id: str,
        action: str,
        audit_opinion: Optional[str],
        idempotency_key: str,
    ) -> InspectionTask:
        task = await InspectionService.get_task_by_id(db, task_id)
        if not task:
            _raise_http_error(
                status.HTTP_404_NOT_FOUND,
                40400,
                f"巡检任务 {task_id} 不存在",
            )

        if task.inspection_type != InspectionType.DAILY:
            _raise_http_error(
                status.HTTP_400_BAD_REQUEST,
                40000,
                f"任务 {task_id} 不是日管控任务",
            )

        if (
            task.last_idempotency_key == idempotency_key
            and task.last_idempotency_action == "DAILY_AUDIT"
        ):
            return task

        if action not in {"PASS", "REJECT"}:
            _raise_http_error(status.HTTP_400_BAD_REQUEST, 40000, "无效的审核动作")

        target_state = (
            InspectionTaskStatus.COMPLETED if action == "PASS"
            else InspectionTaskStatus.REJECTED
        )

        validate_state_transition(
            current_state=task.status,
            target_state=target_state
        )

        now = _utc_now()

        task.status = target_state
        task.approver_id = auditor_id
        task.last_audit_id = auditor_id
        task.last_audit_opinion = audit_opinion
        task.last_audit_time = now

        audit_logs = list(task.audit_logs or [])
        audit_logs.append(
            {
                "auditor_id": auditor_id,
                "action": action,
                "opinion": audit_opinion,
                "audited_at": _utc_iso(now),
            }
        )
        task.audit_logs = audit_logs

        if action == "PASS":
            task.completed_time = now

        task.last_idempotency_key = idempotency_key
        task.last_idempotency_action = "DAILY_AUDIT"

        await db.commit()
        await db.refresh(task)
        return task

    @staticmethod
    async def rectify_daily_task(
        db: AsyncSession,
        task_id: int,
        request: DailyRectifyRequest,
        idempotency_key: str,
    ) -> InspectionTask:
        task = await InspectionService.get_task_by_id(db, task_id)
        if not task:
            _raise_http_error(
                status.HTTP_404_NOT_FOUND,
                40400,
                f"巡检任务 {task_id} 不存在",
            )

        if task.inspection_type != InspectionType.DAILY:
            _raise_http_error(
                status.HTTP_400_BAD_REQUEST,
                40000,
                f"任务 {task_id} 不是日管控任务",
            )

        if (
            task.last_idempotency_key == idempotency_key
            and task.last_idempotency_action == "DAILY_RECTIFY"
        ):
            return task

        validate_state_transition(
            current_state=task.status,
            target_state=InspectionTaskStatus.RECTIFIED
        )

        now = _utc_now()
        items_log = []
        audit_logs = task.audit_logs or []
        for item_feedback in request.feedback_per_item:
            stmt = select(InspectionResult).where(
                InspectionResult.id == item_feedback.result_id,
                InspectionResult.task_id == task_id
            )
            result_record = (await db.execute(stmt)).scalar_one_or_none()

            if result_record:
                result_record.rectification_description = item_feedback.description
                result_record.rectification_photos = item_feedback.photos
                result_record.rectified_at = now
                items_log.append({
                    "result_id": item_feedback.result_id,
                    "item_id": str(result_record.item_id),
                    "description": item_feedback.description,
                    "photos": item_feedback.photos or [],
                })
                
                if item_feedback.description or item_feedback.photos:
                    audit_logs.append({
                        "auditor_id": request.rectifier_id,
                        "action": "RECTIFY",
                        "item_id": str(result_record.item_id),
                        "description": item_feedback.description,
                        "photos": item_feedback.photos,
                        "audited_at": _utc_iso(now),
                    })

        audit_logs.append({
            "action": "RECTIFY",
            "rectifier_id": request.rectifier_id,
            "rectified_at": _utc_iso(now),
            "items": items_log,
        })
        task.audit_logs = audit_logs

        task.status = InspectionTaskStatus.RECTIFIED
        task.rectified_time = now
        task.executor_id = request.rectifier_id

        task.last_idempotency_key = idempotency_key
        task.last_idempotency_action = "DAILY_RECTIFY"

        await db.commit()
        await db.refresh(task)
        return task

    @staticmethod
    async def submit_weekly_task(
        db: AsyncSession,
        task_id: int,
        request: WeeklyInspectionSubmitRequest,
        idempotency_key: str,
        inspector_name: Optional[str] = None,
    ) -> InspectionTask:
        task = await InspectionService.get_task_by_id(db, task_id)
        if not task:
            _raise_http_error(
                status.HTTP_404_NOT_FOUND,
                40400,
                f"巡检任务 {task_id} 不存在",
            )

        if task.inspection_type != InspectionType.WEEKLY:
            _raise_http_error(
                status.HTTP_400_BAD_REQUEST,
                40000,
                f"任务 {task_id} 不是周排查任务",
            )

        if (
            task.last_idempotency_key == idempotency_key
            and task.last_idempotency_action == "WEEKLY_SUBMIT"
        ):
            return task

        validate_state_transition(
            current_state=task.status,
            target_state=InspectionTaskStatus.SUBMITTED
        )

        task.status = InspectionTaskStatus.SUBMITTED
        task.submission_time = _utc_now()
        task.inspector_id = request.inspector_id
        if inspector_name is not None:
            task.executor_name_snapshot = inspector_name
        task.actual_start_time = _ensure_utc(request.actual_start_time)

        await db.execute(
            delete(InspectionResult).where(InspectionResult.task_id == task.id)
        )

        item_ids = [item.item_id for item in request.results]
        item_map = {}
        if item_ids:
            items_stmt = select(InspectionItem).where(InspectionItem.id.in_(item_ids))
            items = (await db.execute(items_stmt)).scalars().all()
            item_map = {item.id: item for item in items}

        total_score = 0.0
        red_line_issues = 0
        for item_data in request.results:
            item = item_map.get(item_data.item_id)
            has_issue = None
            is_red_line_triggered = None
            if item and item.total_score is not None:
                has_issue = item_data.score_given < item.total_score
                if has_issue and item.issue_type == IssueType.RED_LINE:
                    is_red_line_triggered = True
                else:
                    is_red_line_triggered = False

            total_score += float(item_data.score_given or 0)
            if is_red_line_triggered:
                red_line_issues += 1

            result = InspectionResult(
                task_id=task.id,
                item_id=item_data.item_id,
                inspection_type=InspectionType.WEEKLY,
                score_given=item_data.score_given,
                inspection_description=item_data.description,
                inspection_photos=item_data.photos,
                rectification_description=item_data.rectification_description,
                rectification_photos=item_data.rectification_photos,
                has_issue=has_issue,
                is_red_line_triggered=is_red_line_triggered,
            )
            db.add(result)

        task.total_score = total_score
        task.red_line_issues = red_line_issues

        task.last_idempotency_key = idempotency_key
        task.last_idempotency_action = "WEEKLY_SUBMIT"

        await db.commit()
        await db.refresh(task)
        return task

    @staticmethod
    async def rectify_weekly_task(
        db: AsyncSession,
        task_id: int,
        request: WeeklyRectifyRequest,
        idempotency_key: str,
    ) -> InspectionTask:
        task = await InspectionService.get_task_by_id(db, task_id)
        if not task:
            _raise_http_error(
                status.HTTP_404_NOT_FOUND,
                40400,
                f"巡检任务 {task_id} 不存在",
            )

        if task.inspection_type != InspectionType.WEEKLY:
            _raise_http_error(
                status.HTTP_400_BAD_REQUEST,
                40000,
                f"任务 {task_id} 不是周排查任务",
            )

        if (
            task.last_idempotency_key == idempotency_key
            and task.last_idempotency_action == "WEEKLY_RECTIFY"
        ):
            return task

        validate_state_transition(
            current_state=task.status,
            target_state=InspectionTaskStatus.RECTIFIED
        )

        for item_feedback in request.feedback_per_item:
            stmt = select(InspectionResult).where(
                InspectionResult.id == item_feedback.result_id,
                InspectionResult.task_id == task_id
            )
            result_record = (await db.execute(stmt)).scalar_one_or_none()

            if result_record:
                result_record.rectification_description = item_feedback.description
                result_record.rectification_photos = item_feedback.photos
                result_record.rectified_at = _utc_now()

        task.status = InspectionTaskStatus.RECTIFIED
        task.rectified_time = _utc_now()
        task.executor_id = request.rectifier_id

        task.last_idempotency_key = idempotency_key
        task.last_idempotency_action = "WEEKLY_RECTIFY"

        await db.commit()
        await db.refresh(task)
        return task

    @staticmethod
    async def audit_weekly_task(
        db: AsyncSession,
        task_id: int,
        auditor_id: str,
        action: str,
        audit_opinion: Optional[str],
        idempotency_key: str,
    ) -> InspectionTask:
        task = await InspectionService.get_task_by_id(db, task_id)
        if not task:
            _raise_http_error(
                status.HTTP_404_NOT_FOUND,
                40400,
                f"巡检任务 {task_id} 不存在",
            )

        if task.inspection_type != InspectionType.WEEKLY:
            _raise_http_error(
                status.HTTP_400_BAD_REQUEST,
                40000,
                f"任务 {task_id} 不是周排查任务",
            )

        if (
            task.last_idempotency_key == idempotency_key
            and task.last_idempotency_action == "WEEKLY_AUDIT"
        ):
            return task

        if action not in {"PASS", "REJECT"}:
            _raise_http_error(status.HTTP_400_BAD_REQUEST, 40000, "无效的审核动作")

        target_state = (
            InspectionTaskStatus.COMPLETED if action == "PASS"
            else InspectionTaskStatus.REJECTED
        )

        validate_state_transition(
            current_state=task.status,
            target_state=target_state
        )

        now = _utc_now()

        task.status = target_state
        task.approver_id = auditor_id
        task.last_audit_id = auditor_id
        task.last_audit_opinion = audit_opinion
        task.last_audit_time = now

        audit_logs = list(task.audit_logs or [])
        audit_logs.append(
            {
                "auditor_id": auditor_id,
                "action": action,
                "opinion": audit_opinion,
                "audited_at": _utc_iso(now),
            }
        )
        task.audit_logs = audit_logs

        if action == "PASS":
            task.completed_time = now

        task.last_idempotency_key = idempotency_key
        task.last_idempotency_action = "WEEKLY_AUDIT"

        await db.commit()
        await db.refresh(task)
        return task

    @staticmethod
    async def submit_video_task(
        db: AsyncSession,
        task_id: int,
        request: WeeklyInspectionSubmitRequest,
        idempotency_key: str,
        inspector_name: Optional[str] = None,
    ) -> InspectionTask:
        task = await InspectionService.get_task_by_id(db, task_id)
        if not task:
            _raise_http_error(
                status.HTTP_404_NOT_FOUND,
                40400,
                f"巡检任务 {task_id} 不存在",
            )

        if task.inspection_type != InspectionType.VIDEO:
            _raise_http_error(
                status.HTTP_400_BAD_REQUEST,
                40000,
                f"任务 {task_id} 不是视频巡检任务",
            )

        if (
            task.last_idempotency_key == idempotency_key
            and task.last_idempotency_action == "VIDEO_SUBMIT"
        ):
            return task

        validate_state_transition(
            current_state=task.status,
            target_state=InspectionTaskStatus.SUBMITTED,
        )

        task.status = InspectionTaskStatus.SUBMITTED
        task.submission_time = _utc_now()
        task.inspector_id = request.inspector_id
        if inspector_name is not None:
            task.executor_name_snapshot = inspector_name
        task.actual_start_time = _ensure_utc(request.actual_start_time)

        await db.execute(
            delete(InspectionResult).where(InspectionResult.task_id == task.id)
        )

        item_ids = [item.item_id for item in request.results]
        item_map = {}
        if item_ids:
            items_stmt = select(InspectionItem).where(InspectionItem.id.in_(item_ids))
            items = (await db.execute(items_stmt)).scalars().all()
            item_map = {item.id: item for item in items}

        total_score = 0.0
        red_line_issues = 0
        for item_data in request.results:
            item = item_map.get(item_data.item_id)
            has_issue = None
            is_red_line_triggered = None
            if item and item.total_score is not None:
                has_issue = item_data.score_given < item.total_score
                if has_issue and item.issue_type == IssueType.RED_LINE:
                    is_red_line_triggered = True
                else:
                    is_red_line_triggered = False

            total_score += float(item_data.score_given or 0)
            if is_red_line_triggered:
                red_line_issues += 1

            result = InspectionResult(
                task_id=task.id,
                item_id=item_data.item_id,
                inspection_type=InspectionType.VIDEO,
                score_given=item_data.score_given,
                inspection_description=item_data.description,
                inspection_photos=item_data.photos,
                has_issue=has_issue,
                is_red_line_triggered=is_red_line_triggered,
            )
            db.add(result)

        task.total_score = total_score
        task.red_line_issues = red_line_issues
        task.last_idempotency_key = idempotency_key
        task.last_idempotency_action = "VIDEO_SUBMIT"

        await db.commit()
        await db.refresh(task)
        return task

    @staticmethod
    async def rectify_video_task(
        db: AsyncSession,
        task_id: int,
        request: WeeklyRectifyRequest,
        idempotency_key: str,
    ) -> InspectionTask:
        task = await InspectionService.get_task_by_id(db, task_id)
        if not task:
            _raise_http_error(
                status.HTTP_404_NOT_FOUND,
                40400,
                f"巡检任务 {task_id} 不存在",
            )

        if task.inspection_type != InspectionType.VIDEO:
            _raise_http_error(
                status.HTTP_400_BAD_REQUEST,
                40000,
                f"任务 {task_id} 不是视频巡检任务",
            )

        if (
            task.last_idempotency_key == idempotency_key
            and task.last_idempotency_action == "VIDEO_RECTIFY"
        ):
            return task

        validate_state_transition(
            current_state=task.status,
            target_state=InspectionTaskStatus.RECTIFIED,
        )

        for item_feedback in request.feedback_per_item:
            stmt = select(InspectionResult).where(
                InspectionResult.id == item_feedback.result_id,
                InspectionResult.task_id == task_id,
            )
            result_record = (await db.execute(stmt)).scalar_one_or_none()

            if result_record:
                result_record.rectification_description = item_feedback.description
                result_record.rectification_photos = item_feedback.photos
                result_record.rectified_at = _utc_now()

        task.status = InspectionTaskStatus.RECTIFIED
        task.rectified_time = _utc_now()
        task.executor_id = request.rectifier_id

        task.last_idempotency_key = idempotency_key
        task.last_idempotency_action = "VIDEO_RECTIFY"

        await db.commit()
        await db.refresh(task)
        return task

    @staticmethod
    async def audit_video_task(
        db: AsyncSession,
        task_id: int,
        auditor_id: str,
        action: str,
        audit_opinion: Optional[str],
        idempotency_key: str,
    ) -> InspectionTask:
        task = await InspectionService.get_task_by_id(db, task_id)
        if not task:
            _raise_http_error(
                status.HTTP_404_NOT_FOUND,
                40400,
                f"巡检任务 {task_id} 不存在",
            )

        if task.inspection_type != InspectionType.VIDEO:
            _raise_http_error(
                status.HTTP_400_BAD_REQUEST,
                40000,
                f"任务 {task_id} 不是视频巡检任务",
            )

        if (
            task.last_idempotency_key == idempotency_key
            and task.last_idempotency_action == "VIDEO_AUDIT"
        ):
            return task

        if action not in {"PASS", "REJECT"}:
            _raise_http_error(status.HTTP_400_BAD_REQUEST, 40000, "无效的审核动作")

        target_state = (
            InspectionTaskStatus.COMPLETED if action == "PASS"
            else InspectionTaskStatus.REJECTED
        )

        validate_state_transition(
            current_state=task.status,
            target_state=target_state,
        )

        now = _utc_now()

        task.status = target_state
        task.approver_id = auditor_id
        task.last_audit_id = auditor_id
        task.last_audit_opinion = audit_opinion
        task.last_audit_time = now

        audit_logs = list(task.audit_logs or [])
        audit_logs.append(
            {
                "auditor_id": auditor_id,
                "action": action,
                "opinion": audit_opinion,
                "audited_at": _utc_iso(now),
            }
        )
        task.audit_logs = audit_logs

        if action == "PASS":
            task.completed_time = now

        task.last_idempotency_key = idempotency_key
        task.last_idempotency_action = "VIDEO_AUDIT"

        await db.commit()
        await db.refresh(task)
        return task

    @staticmethod
    async def submit_joint_task(
        db: AsyncSession,
        task_id: int,
        request: WeeklyInspectionSubmitRequest,
        idempotency_key: str,
        inspector_name: Optional[str] = None,
    ) -> InspectionTask:
        task = await InspectionService.get_task_by_id(db, task_id)
        if not task:
            _raise_http_error(status.HTTP_404_NOT_FOUND, 40400, f"巡检任务 {task_id} 不存在")

        if task.inspection_type != InspectionType.JOINT:
            _raise_http_error(status.HTTP_400_BAD_REQUEST, 40000, f"任务 {task_id} 不是联合巡检任务")

        if task.last_idempotency_key == idempotency_key and task.last_idempotency_action == "JOINT_SUBMIT":
            return task

        validate_state_transition(current_state=task.status, target_state=InspectionTaskStatus.SUBMITTED)

        task.status = InspectionTaskStatus.SUBMITTED
        task.submission_time = _utc_now()
        task.inspector_id = request.inspector_id
        if inspector_name is not None:
            task.executor_name_snapshot = inspector_name
        task.actual_start_time = _ensure_utc(request.actual_start_time)

        await db.execute(delete(InspectionResult).where(InspectionResult.task_id == task.id))

        item_ids = [item.item_id for item in request.results]
        item_map = {}
        if item_ids:
            items_stmt = select(InspectionItem).where(InspectionItem.id.in_(item_ids))
            items = (await db.execute(items_stmt)).scalars().all()
            item_map = {item.id: item for item in items}

        total_score = 0.0
        red_line_issues = 0
        for item_data in request.results:
            item = item_map.get(item_data.item_id)
            has_issue = None
            is_red_line_triggered = None
            if item and item.total_score is not None:
                has_issue = item_data.score_given < item.total_score
                if has_issue and item.issue_type == IssueType.RED_LINE:
                    is_red_line_triggered = True
                else:
                    is_red_line_triggered = False

            total_score += float(item_data.score_given or 0)
            if is_red_line_triggered:
                red_line_issues += 1

            result = InspectionResult(
                task_id=task.id,
                item_id=item_data.item_id,
                inspection_type=InspectionType.JOINT,
                score_given=item_data.score_given,
                inspection_description=item_data.description,
                inspection_photos=item_data.photos,
                has_issue=has_issue,
                is_red_line_triggered=is_red_line_triggered,
            )
            db.add(result)

        task.total_score = total_score
        task.red_line_issues = red_line_issues
        task.last_idempotency_key = idempotency_key
        task.last_idempotency_action = "JOINT_SUBMIT"

        await db.commit()
        await db.refresh(task)
        return task

    @staticmethod
    async def rectify_joint_task(
        db: AsyncSession,
        task_id: int,
        request: WeeklyRectifyRequest,
        idempotency_key: str,
    ) -> InspectionTask:
        task = await InspectionService.get_task_by_id(db, task_id)
        if not task:
            _raise_http_error(status.HTTP_404_NOT_FOUND, 40400, f"巡检任务 {task_id} 不存在")

        if task.inspection_type != InspectionType.JOINT:
            _raise_http_error(status.HTTP_400_BAD_REQUEST, 40000, f"任务 {task_id} 不是联合巡检任务")

        if task.last_idempotency_key == idempotency_key and task.last_idempotency_action == "JOINT_RECTIFY":
            return task

        validate_state_transition(current_state=task.status, target_state=InspectionTaskStatus.RECTIFIED)

        for item_feedback in request.feedback_per_item:
            stmt = select(InspectionResult).where(
                InspectionResult.id == item_feedback.result_id,
                InspectionResult.task_id == task_id
            )
            result_record = (await db.execute(stmt)).scalar_one_or_none()

            if result_record:
                result_record.rectification_description = item_feedback.description
                result_record.rectification_photos = item_feedback.photos
                result_record.rectified_at = _utc_now()

        task.status = InspectionTaskStatus.RECTIFIED
        task.rectified_time = _utc_now()
        task.executor_id = request.rectifier_id
        task.last_idempotency_key = idempotency_key
        task.last_idempotency_action = "JOINT_RECTIFY"

        await db.commit()
        await db.refresh(task)
        return task

    @staticmethod
    async def audit_joint_task(
        db: AsyncSession,
        task_id: int,
        auditor_id: str,
        action: str,
        audit_opinion: Optional[str],
        idempotency_key: str,
    ) -> InspectionTask:
        task = await InspectionService.get_task_by_id(db, task_id)
        if not task:
            _raise_http_error(status.HTTP_404_NOT_FOUND, 40400, f"巡检任务 {task_id} 不存在")

        if task.inspection_type != InspectionType.JOINT:
            _raise_http_error(status.HTTP_400_BAD_REQUEST, 40000, f"任务 {task_id} 不是联合巡检任务")

        if task.last_idempotency_key == idempotency_key and task.last_idempotency_action == "JOINT_AUDIT":
            return task

        if action not in {"PASS", "REJECT"}:
            _raise_http_error(status.HTTP_400_BAD_REQUEST, 40000, "无效的审核动作")

        target_state = InspectionTaskStatus.COMPLETED if action == "PASS" else InspectionTaskStatus.REJECTED
        validate_state_transition(current_state=task.status, target_state=target_state)

        now = _utc_now()
        task.status = target_state
        task.approver_id = auditor_id
        task.last_audit_id = auditor_id
        task.last_audit_opinion = audit_opinion
        task.last_audit_time = now

        audit_logs = list(task.audit_logs or [])
        audit_logs.append({
            "auditor_id": auditor_id,
            "action": action,
            "opinion": audit_opinion,
            "audited_at": _utc_iso(now),
        })
        task.audit_logs = audit_logs

        if action == "PASS":
            task.completed_time = now

        task.last_idempotency_key = idempotency_key
        task.last_idempotency_action = "JOINT_AUDIT"

        await db.commit()
        await db.refresh(task)
        return task

class InspectionServiceSync:
    @staticmethod
    def submit_task(db: Session, task_id: int) -> InspectionTask:
        task = InspectionService.get_task_by_id_sync(db, task_id)
        if not task:
            _raise_http_error(
                status.HTTP_404_NOT_FOUND,
                40400,
                f"巡检任务 {task_id} 不存在",
            )

        validate_state_transition(
            current_state=task.status,
            target_state=InspectionTaskStatus.SUBMITTED
        )

        task.status = InspectionTaskStatus.SUBMITTED
        task.submission_time = _utc_now()
        db.commit()
        db.refresh(task)
        return task

class InspectionWorkflow:
    """巡检工作流公共方法"""
    @staticmethod
    async def submit_task(
        db: AsyncSession,
        task_id: int,
        request,
        idempotency_key: str,
        inspection_type: InspectionType,
        inspector_name: Optional[str] = None
    ) -> InspectionTask:
        if inspection_type == InspectionType.DAILY:
            return await InspectionService.submit_daily_task(db, task_id, request, idempotency_key)
        elif inspection_type == InspectionType.WEEKLY:
            return await InspectionService.submit_weekly_task(db, task_id, request, idempotency_key, inspector_name)
        elif inspection_type == InspectionType.VIDEO:
            return await InspectionService.submit_video_task(db, task_id, request, idempotency_key, inspector_name)
        elif inspection_type == InspectionType.JOINT:
            return await InspectionService.submit_joint_task(db, task_id, request, idempotency_key, inspector_name)
        else:
            raise ValueError(f"不支持的巡检类型: {inspection_type}")

    @staticmethod
    async def audit_task(
        db: AsyncSession,
        task_id: int,
        auditor_id: str,
        action: str,
        audit_opinion: Optional[str],
        idempotency_key: str,
        inspection_type: InspectionType
    ) -> InspectionTask:
        if inspection_type == InspectionType.DAILY:
            return await InspectionService.audit_daily_task(db, task_id, auditor_id, action, audit_opinion, idempotency_key)
        elif inspection_type == InspectionType.WEEKLY:
            return await InspectionService.audit_weekly_task(db, task_id, auditor_id, action, audit_opinion, idempotency_key)
        elif inspection_type == InspectionType.VIDEO:
            return await InspectionService.audit_video_task(db, task_id, auditor_id, action, audit_opinion, idempotency_key)
        elif inspection_type == InspectionType.JOINT:
            return await InspectionService.audit_joint_task(db, task_id, auditor_id, action, audit_opinion, idempotency_key)
        else:
            raise ValueError(f"不支持的巡检类型: {inspection_type}")

    @staticmethod
    async def rectify_task(
        db: AsyncSession,
        task_id: int,
        request,
        idempotency_key: str,
        inspection_type: InspectionType
    ) -> InspectionTask:
        if inspection_type == InspectionType.DAILY:
            return await InspectionService.rectify_daily_task(db, task_id, request, idempotency_key)
        elif inspection_type == InspectionType.WEEKLY:
            return await InspectionService.rectify_weekly_task(db, task_id, request, idempotency_key)
        elif inspection_type == InspectionType.VIDEO:
            return await InspectionService.rectify_video_task(db, task_id, request, idempotency_key)
        elif inspection_type == InspectionType.JOINT:
            return await InspectionService.rectify_joint_task(db, task_id, request, idempotency_key)
        else:
            raise ValueError(f"不支持的巡检类型: {inspection_type}")

class JointInspectionService:
    @staticmethod
    async def sign_task(
        db: AsyncSession,
        task_id: int,
        participant_id: str,
        signature: str,
        idempotency_key: str
    ) -> InspectionTask:
        task = await InspectionService.get_task_by_id(db, task_id)
        if not task:
            _raise_http_error(status.HTTP_404_NOT_FOUND, 40400, f"任务 {task_id} 不存在")
        if task.inspection_type != InspectionType.JOINT:
            _raise_http_error(status.HTTP_400_BAD_REQUEST, 40000, "该任务不是联合巡检任务")
        if task.last_idempotency_key == idempotency_key and task.last_idempotency_action == "JOINT_SIGN":
            return task
        
        participant_ids = task.joint_participant_ids or []
        if participant_id not in participant_ids:
            _raise_http_error(status.HTTP_403_FORBIDDEN, 40300, "该用户不是联合巡检参与人")
        
        signatures = dict(task.joint_signatures) if task.joint_signatures else {}
        if participant_id in signatures:
            _raise_http_error(status.HTTP_409_CONFLICT, 40900, "该参与人已签字")
            
        signatures[participant_id] = {
            "signature_url": signature,
            "signed_at": _utc_iso(_utc_now()),
            "signed_by": participant_id
        }
        
        task.joint_signatures = signatures
        task.last_idempotency_key = idempotency_key
        task.last_idempotency_action = "JOINT_SIGN"
        
        await db.commit()
        await db.refresh(task)
        return task

class MonthlyReportService:
    @staticmethod
    async def preview_aggregation(
        db: AsyncSession,
        start_date: str,
        end_date: str,
        canteen_ids: List[int]
    ) -> dict:
        stmt = select(InspectionTask).where(
            InspectionTask.business_date >= start_date,
            InspectionTask.business_date <= end_date,
            InspectionTask.canteen_id.in_(canteen_ids),
            InspectionTask.status == InspectionTaskStatus.COMPLETED
        )
        tasks = (await db.execute(stmt)).scalars().all()
        
        if not tasks:
            return {
                "period": {"start": start_date, "end": end_date},
                "canteen_summary": [],
                "issue_ranking": [],
                "rectification_rate": {"total": 0.0, "by_canteen": {}},
                "generated_at": _utc_iso(_utc_now())
            }
        
        task_ids = [t.id for t in tasks]
        result_stmt = select(InspectionResult).where(InspectionResult.task_id.in_(task_ids))
        results = (await db.execute(result_stmt)).scalars().all()
        
        task_results_map: Dict[int, List[InspectionResult]] = {}
        for r in results:
            task_results_map.setdefault(r.task_id, []).append(r)
            
        canteen_summary_map = {}
        for task in tasks:
            canteen_id = task.canteen_id
            task_results = task_results_map.get(task.id, [])
            issue_count = sum(1 for r in task_results if r.has_issue or r.is_qualified is False)
            
            if canteen_id not in canteen_summary_map:
                canteen_summary_map[canteen_id] = {
                    "canteen_id": canteen_id,
                    "canteen_name": task.canteen_name_snapshot,
                    "task_count": 0,
                    "issue_count": 0,
                    "total_score": 0.0,
                    "rectification_rate": 0.0
                }
            
            summary = canteen_summary_map[canteen_id]
            summary["task_count"] += 1
            summary["issue_count"] += issue_count
            if task.total_score is not None:
                summary["total_score"] = (summary["total_score"] or 0) + task.total_score
                
        for summary in canteen_summary_map.values():
            if summary["issue_count"] > 0:
                canteen_task_ids = [t.id for t in tasks if t.canteen_id == summary["canteen_id"]]
                canteen_results = [r for rid in canteen_task_ids for r in task_results_map.get(rid, [])]
                issues = [r for r in canteen_results if r.has_issue or r.is_qualified is False]
                rectified = [r for r in issues if r.rectified_at is not None]
                summary["rectification_rate"] = (len(rectified) / len(issues) * 100) if issues else 100.0
                
        issue_count_by_item = {}
        item_canteen_map = {}
        for r in results:
            if r.has_issue or r.is_qualified is False:
                issue_count_by_item[r.item_id] = issue_count_by_item.get(r.item_id, 0) + 1
                item_canteen_map.setdefault(r.item_id, set()).add(r.task_id)
                
        item_ids_list = list(issue_count_by_item.keys())
        item_map = {}
        if item_ids_list:
            item_stmt = select(InspectionItem).where(InspectionItem.id.in_(item_ids_list))
            items = (await db.execute(item_stmt)).scalars().all()
            item_map = {i.id: i.content for i in items}
            
        sorted_issues = sorted(issue_count_by_item.items(), key=lambda x: x[1], reverse=True)[:5]
        issue_ranking = [
            {
                "item_id": item_id,
                "content": item_map.get(item_id, f"巡检项{item_id}"),
                "issue_count": count,
                "canteen_ids": list(item_canteen_map.get(item_id, set()))
            }
            for item_id, count in sorted_issues
        ]
        
        total_issues = len([r for r in results if r.has_issue or r.is_qualified is False])
        total_rectified = len([r for r in results if r.rectified_at is not None])
        overall_rate = (total_rectified / total_issues * 100) if total_issues > 0 else 100.0
        
        by_canteen_rates = {
            str(s["canteen_id"]): round(s["rectification_rate"], 2) 
            for s in canteen_summary_map.values()
        }
        
        return {
            "period": {"start": start_date, "end": end_date},
            "canteen_summary": list(canteen_summary_map.values()),
            "issue_ranking": issue_ranking,
            "rectification_rate": {
                "total": round(overall_rate, 2),
                "by_canteen": by_canteen_rates
            },
            "generated_at": _utc_iso(_utc_now())
        }

    @staticmethod
    async def generate_export(
        db: AsyncSession,
        start_date: str,
        end_date: str,
        canteen_ids: List[int],
        export_format: str = "pdf"
    ) -> bytes:
        # Mocking PDF generation
        return b"%PDF-1.4\n%Mock PDF Content"

    @staticmethod
    async def save_offline_report(
        db: AsyncSession,
        title: str,
        canteen_id: int,
        canteen_name: str,
        reporter_id: str,
        reporter_name: str,
        file_url: str,
        remark: Optional[str] = None,
        tenant_id: Optional[int] = None
    ):
        from app.modules.inspection.models import MonthlyReport
        report = MonthlyReport(
            title=title,
            canteen_id=canteen_id,
            canteen_name_snapshot=canteen_name,
            reporter_id=reporter_id,
            reporter_name_snapshot=reporter_name,
            offline_report_url=file_url,
            offline_report_uploaded_at=_utc_now(),
            report_time=_utc_now(),
            remark=remark,
            source_config={"type": "offline_upload"}
        )
        if tenant_id is not None:
            report.tenant_id = tenant_id
        db.add(report)
        await db.commit()
        await db.refresh(report)
        return report

    @staticmethod
    async def delete_report(
        db: AsyncSession,
        report_id: int,
        tenant_id: int
    ) -> bool:
        from app.modules.inspection.models import MonthlyReport
        stmt = select(MonthlyReport).where(
            MonthlyReport.id == report_id,
            MonthlyReport.is_deleted == False
        )
        result = await db.execute(stmt)
        report = result.scalar_one_or_none()
        
        if not report:
            return False
        
        report.is_deleted = True
        await db.commit()
        return True

    @staticmethod
    async def get_file_key_info(
        db: AsyncSession,
        file_key: str
    ) -> Optional[dict]:
        from app.modules.inspection.models import MonthlyReport
        stmt = select(MonthlyReport).where(
            MonthlyReport.offline_report_url == file_key,
            MonthlyReport.is_deleted == False
        )
        result = await db.execute(stmt)
        report = result.scalar_one_or_none()
        return {"file_key": file_key, "report_id": report.id} if report else None

    @staticmethod
    async def list_reports(
        db: AsyncSession,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        canteen_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> dict:
        from app.modules.inspection.models import MonthlyReport
        filters = [MonthlyReport.is_deleted == False]
        if start_date:
            filters.append(MonthlyReport.report_time >= start_date)
        if end_date:
            filters.append(MonthlyReport.report_time <= end_date)
        if canteen_id:
            filters.append(MonthlyReport.canteen_id == canteen_id)
            
        count_stmt = select(func.count()).select_from(MonthlyReport).where(*filters)
        total = (await db.execute(count_stmt)).scalar_one()
        
        stmt = select(MonthlyReport).where(*filters).order_by(MonthlyReport.report_time.desc()).offset((page - 1) * page_size).limit(page_size)
        reports = (await db.execute(stmt)).scalars().all()
        
        items = []
        for r in reports:
            items.append({
                "id": r.id,
                "title": r.title,
                "canteen_name": r.canteen_name_snapshot,
                "reporter_name": r.reporter_name_snapshot,
                "report_time": _utc_iso(r.report_time) if r.report_time else None,
                "source_type": "offline" if r.offline_report_url else "system",
                "offline_report_url": r.offline_report_url or None,
                "system_generated_at": _utc_iso(r.system_generated_at) if r.system_generated_at else None,
                "offline_report_uploaded_at": _utc_iso(r.offline_report_uploaded_at) if r.offline_report_uploaded_at else None,
            })
            
        return {"total": total, "list": items}


def _extract_target_node_ids(value: Optional[Dict[str, Any]]) -> List[int]:
    if isinstance(value, dict):
        raw = value.get("raw")
        if isinstance(raw, list):
            return [item for item in raw if isinstance(item, int)]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, int)]
    return []


async def _expand_canteen_ids(
    db: AsyncSession,
    tenant_id: int,
    node_ids: List[int],
) -> List[int]:
    orgs = (
        await db.execute(
            select(OrgModel).where(OrgModel.tenant_id == tenant_id)
        )
    ).scalars().all()

    if not orgs:
        return []

    org_map: Dict[int, OrgModel] = {org.id: org for org in orgs}
    children_map: Dict[Optional[int], List[int]] = {}
    for org in orgs:
        children_map.setdefault(org.parent_id, []).append(org.id)

    canteen_ids: Set[int] = set()

    for node_id in node_ids:
        if node_id not in org_map:
            _raise_http_error(
                status.HTTP_400_BAD_REQUEST,
                40000,
                f"目标节点 {node_id} 不存在",
            )
        stack = [node_id]
        while stack:
            current_id = stack.pop()
            org = org_map[current_id]
            if org.org_type == "CANTEEN":
                canteen_ids.add(org.id)
                continue
            stack.extend(children_map.get(current_id, []))

    return sorted(canteen_ids)


def _build_target_node_ids_raw(
    raw_ids: List[int],
    expanded_ids: List[int],
) -> Dict[str, Any]:
    return {
        "raw": raw_ids,
        "expanded_canteen_ids": expanded_ids,
    }


class InspectionTemplateService:
    @staticmethod
    async def list_templates(
        db: AsyncSession,
        tenant_id_or_inspection_type,
        inspection_type_or_page,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> dict:
        if isinstance(tenant_id_or_inspection_type, InspectionType):
            tenant_id = None
            inspection_type = tenant_id_or_inspection_type
            resolved_page = int(inspection_type_or_page)
            resolved_page_size = int(page) if page is not None else 20
        else:
            tenant_id = int(tenant_id_or_inspection_type)
            inspection_type = inspection_type_or_page
            resolved_page = int(page) if page is not None else 1
            resolved_page_size = int(page_size) if page_size is not None else 20

        filters = [InspectionTemplate.inspection_type == inspection_type]
        if tenant_id is not None:
            filters.append(InspectionTemplate.tenant_id == tenant_id)

        count_stmt = select(func.count()).select_from(InspectionTemplate).where(
            *filters
        )
        total = (await db.execute(count_stmt)).scalar_one()
        stmt = (
            select(InspectionTemplate)
            .where(*filters)
            .order_by(InspectionTemplate.created_at.desc())
            .offset((resolved_page - 1) * resolved_page_size)
            .limit(resolved_page_size)
        )
        records = (await db.execute(stmt)).scalars().all()
        return {"total": total, "records": records}

    @staticmethod
    async def get_template(
        db: AsyncSession,
        tenant_id_or_template_id,
        template_id_or_inspection_type,
        inspection_type: Optional[InspectionType] = None,
    ) -> InspectionTemplate:
        if isinstance(template_id_or_inspection_type, InspectionType):
            tenant_id = None
            template_id = int(tenant_id_or_template_id)
            resolved_inspection_type = template_id_or_inspection_type
        else:
            tenant_id = int(tenant_id_or_template_id)
            template_id = int(template_id_or_inspection_type)
            resolved_inspection_type = inspection_type

        filters = [
            InspectionTemplate.id == template_id,
            InspectionTemplate.inspection_type == resolved_inspection_type,
        ]
        if tenant_id is not None:
            filters.append(InspectionTemplate.tenant_id == tenant_id)

        stmt = (
            select(InspectionTemplate)
            .where(*filters)
            .options(selectinload(InspectionTemplate.items))
        )
        template = (await db.execute(stmt)).scalar_one_or_none()
        if not template:
            _raise_http_error(status.HTTP_404_NOT_FOUND, 40400, "模板不存在")
        return template

    @staticmethod
    async def create_daily_template(
        db: AsyncSession,
        current_user,
        request: DailyTemplateRequest,
    ) -> InspectionTemplate:
        expanded_ids = await _expand_canteen_ids(
            db, current_user.tenant_id, request.target_node_ids
        )
        template = InspectionTemplate(
            tenant_id=current_user.tenant_id,
            inspection_type=InspectionType.DAILY,
            template_name=request.template_name,
            executor_role=request.executor_role,
            approver_role=request.approver_role,
            form_type=None,
            start_time=request.start_time,
            end_time=request.end_time,
            target_node_ids_raw=_build_target_node_ids_raw(
                request.target_node_ids, expanded_ids
            ),
        )
        db.add(template)
        await db.flush()

        for item in request.items:
            db.add(
                InspectionItem(
                    tenant_id=current_user.tenant_id,
                    template_id=template.id,
                    parent_item_id=None,
                    item_type=ItemType.ITEM,
                    sort_order=item.sort_order,
                    content=item.content,
                    completion_method=item.completion_method,
                    is_active=True,
                )
            )

        await db.commit()
        await db.refresh(template)
        return template

    @staticmethod
    async def create_weekly_template(
        db: AsyncSession,
        current_user,
        request: WeeklyTemplateRequest,
    ) -> InspectionTemplate:
        expanded_ids = await _expand_canteen_ids(
            db, current_user.tenant_id, request.target_node_ids
        )
        template = InspectionTemplate(
            tenant_id=current_user.tenant_id,
            inspection_type=InspectionType.WEEKLY,
            template_name=request.template_name,
            executor_role=request.executor_role,
            approver_role=request.approver_role,
            form_type=request.form_type,
            start_time=request.start_time,
            end_time=request.end_time,
            target_node_ids_raw=_build_target_node_ids_raw(
                request.target_node_ids, expanded_ids
            ),
        )
        db.add(template)
        await db.flush()

        for major in request.major_items:
            group_item = InspectionItem(
                tenant_id=current_user.tenant_id,
                template_id=template.id,
                parent_item_id=None,
                item_type=ItemType.GROUP,
                sort_order=major.sort_order,
                content=major.title,
                is_active=True,
            )
            db.add(group_item)
            await db.flush()
            for minor in major.minor_items:
                db.add(
                    InspectionItem(
                        tenant_id=current_user.tenant_id,
                        template_id=template.id,
                        parent_item_id=group_item.id,
                        item_type=ItemType.ITEM,
                        sort_order=minor.sort_order,
                        content=minor.content,
                        issue_type=minor.issue_type,
                        total_score=minor.total_score,
                        scoring_options=minor.scoring_options,
                        is_active=True,
                    )
                )

        await db.commit()
        await db.refresh(template)
        return template

    @staticmethod
    async def create_joint_template(
        db: AsyncSession,
        current_user,
        request: WeeklyTemplateRequest,
    ) -> InspectionTemplate:
        expanded_ids = await _expand_canteen_ids(
            db, current_user.tenant_id, request.target_node_ids
        )
        template = InspectionTemplate(
            tenant_id=current_user.tenant_id,
            inspection_type=InspectionType.JOINT,
            template_name=request.template_name,
            executor_role=request.executor_role,
            approver_role=request.approver_role,
            form_type=request.form_type,
            start_time=request.start_time,
            end_time=request.end_time,
            target_node_ids_raw=_build_target_node_ids_raw(
                request.target_node_ids, expanded_ids
            ),
        )
        db.add(template)
        await db.flush()

        for major in request.major_items:
            group_item = InspectionItem(
                tenant_id=current_user.tenant_id,
                template_id=template.id,
                parent_item_id=None,
                item_type=ItemType.GROUP,
                sort_order=major.sort_order,
                content=major.title,
                is_active=True,
            )
            db.add(group_item)
            await db.flush()
            for minor in major.minor_items:
                db.add(
                    InspectionItem(
                        tenant_id=current_user.tenant_id,
                        template_id=template.id,
                        parent_item_id=group_item.id,
                        item_type=ItemType.ITEM,
                        sort_order=minor.sort_order,
                        content=minor.content,
                        issue_type=minor.issue_type,
                        total_score=minor.total_score,
                        scoring_options=minor.scoring_options,
                        is_active=True,
                    )
                )

        await db.commit()
        await db.refresh(template)
        return template

    @staticmethod
    async def create_video_template(
        db: AsyncSession,
        current_user,
        request: VideoTemplateRequest,
    ) -> InspectionTemplate:
        expanded_ids = await _expand_canteen_ids(
            db, current_user.tenant_id, request.target_node_ids
        )
        template = InspectionTemplate(
            tenant_id=current_user.tenant_id,
            inspection_type=InspectionType.VIDEO,
            template_name=request.template_name,
            executor_role=request.executor_role,
            approver_role=request.approver_role,
            form_type=request.form_type,
            start_time=request.start_time,
            end_time=request.end_time,
            target_node_ids_raw=_build_target_node_ids_raw(
                request.target_node_ids, expanded_ids
            ),
        )
        db.add(template)
        await db.flush()

        for major in request.major_items:
            group_item = InspectionItem(
                tenant_id=current_user.tenant_id,
                template_id=template.id,
                parent_item_id=None,
                item_type=ItemType.GROUP,
                sort_order=major.sort_order,
                content=major.title,
                is_active=True,
            )
            db.add(group_item)
            await db.flush()
            for minor in major.minor_items:
                db.add(
                    InspectionItem(
                        tenant_id=current_user.tenant_id,
                        template_id=template.id,
                        parent_item_id=group_item.id,
                        item_type=ItemType.ITEM,
                        sort_order=minor.sort_order,
                        content=minor.content,
                        issue_type=minor.issue_type,
                        total_score=minor.total_score,
                        scoring_options=minor.scoring_options,
                        associated_camera_ids=minor.associated_camera_ids,
                        is_active=True,
                    )
                )

        await db.commit()
        await db.refresh(template)
        return template

    @staticmethod
    async def update_daily_template(
        db: AsyncSession,
        template_id: int,
        current_user,
        request: DailyTemplateRequest,
    ) -> InspectionTemplate:
        template = await InspectionTemplateService.get_template(
            db, template_id, InspectionType.DAILY
        )
        expanded_ids = await _expand_canteen_ids(
            db, current_user.tenant_id, request.target_node_ids
        )
        template.template_name = request.template_name
        template.executor_role = request.executor_role
        template.approver_role = request.approver_role
        template.start_time = request.start_time
        template.end_time = request.end_time
        template.target_node_ids_raw = _build_target_node_ids_raw(
            request.target_node_ids, expanded_ids
        )
        template.version = (template.version or 0) + 1

        await db.execute(
            delete(InspectionItem).where(InspectionItem.template_id == template.id)
        )

        for item in request.items:
            db.add(
                InspectionItem(
                    tenant_id=current_user.tenant_id,
                    template_id=template.id,
                    parent_item_id=None,
                    item_type=ItemType.ITEM,
                    sort_order=item.sort_order,
                    content=item.content,
                    completion_method=item.completion_method,
                    is_active=True,
                )
            )

        await db.commit()
        await db.refresh(template)
        return template

    @staticmethod
    async def update_weekly_template(
        db: AsyncSession,
        template_id: int,
        current_user,
        request: WeeklyTemplateRequest,
        inspection_type: InspectionType = InspectionType.WEEKLY,
    ) -> InspectionTemplate:
        template = await InspectionTemplateService.get_template(
            db, template_id, inspection_type
        )
        expanded_ids = await _expand_canteen_ids(
            db, current_user.tenant_id, request.target_node_ids
        )
        template.template_name = request.template_name
        template.executor_role = request.executor_role
        template.approver_role = request.approver_role
        template.form_type = request.form_type
        template.start_time = request.start_time
        template.end_time = request.end_time
        template.target_node_ids_raw = _build_target_node_ids_raw(
            request.target_node_ids, expanded_ids
        )
        template.version = (template.version or 0) + 1

        await db.execute(
            delete(InspectionItem).where(InspectionItem.template_id == template.id)
        )

        for major in request.major_items:
            group_item = InspectionItem(
                tenant_id=current_user.tenant_id,
                template_id=template.id,
                parent_item_id=None,
                item_type=ItemType.GROUP,
                sort_order=major.sort_order,
                content=major.title,
                is_active=True,
            )
            db.add(group_item)
            await db.flush()
            for minor in major.minor_items:
                db.add(
                    InspectionItem(
                        tenant_id=current_user.tenant_id,
                        template_id=template.id,
                        parent_item_id=group_item.id,
                        item_type=ItemType.ITEM,
                        sort_order=minor.sort_order,
                        content=minor.content,
                        issue_type=minor.issue_type,
                        total_score=minor.total_score,
                        scoring_options=minor.scoring_options,
                        is_active=True,
                    )
                )

        await db.commit()
        await db.refresh(template)
        return template

    @staticmethod
    async def update_joint_template(
        db: AsyncSession,
        template_id: int,
        current_user,
        request: WeeklyTemplateRequest,
    ) -> InspectionTemplate:
        template = await InspectionTemplateService.get_template(
            db, template_id, InspectionType.JOINT
        )
        expanded_ids = await _expand_canteen_ids(
            db, current_user.tenant_id, request.target_node_ids
        )
        template.template_name = request.template_name
        template.executor_role = request.executor_role
        template.approver_role = request.approver_role
        template.form_type = request.form_type
        template.start_time = request.start_time
        template.end_time = request.end_time
        template.target_node_ids_raw = _build_target_node_ids_raw(
            request.target_node_ids, expanded_ids
        )
        template.version = (template.version or 0) + 1

        await db.execute(
            delete(InspectionItem).where(InspectionItem.template_id == template.id)
        )

        for major in request.major_items:
            group_item = InspectionItem(
                tenant_id=current_user.tenant_id,
                template_id=template.id,
                parent_item_id=None,
                item_type=ItemType.GROUP,
                sort_order=major.sort_order,
                content=major.title,
                is_active=True,
            )
            db.add(group_item)
            await db.flush()
            for minor in major.minor_items:
                db.add(
                    InspectionItem(
                        tenant_id=current_user.tenant_id,
                        template_id=template.id,
                        parent_item_id=group_item.id,
                        item_type=ItemType.ITEM,
                        sort_order=minor.sort_order,
                        content=minor.content,
                        issue_type=minor.issue_type,
                        total_score=minor.total_score,
                        scoring_options=minor.scoring_options,
                        is_active=True,
                    )
                )

        await db.commit()
        await db.refresh(template)
        return template

    @staticmethod
    async def update_video_template(
        db: AsyncSession,
        template_id: int,
        current_user,
        request: VideoTemplateRequest,
    ) -> InspectionTemplate:
        template = await InspectionTemplateService.get_template(
            db, template_id, InspectionType.VIDEO
        )
        expanded_ids = await _expand_canteen_ids(
            db, current_user.tenant_id, request.target_node_ids
        )
        template.template_name = request.template_name
        template.executor_role = request.executor_role
        template.approver_role = request.approver_role
        template.form_type = request.form_type
        template.start_time = request.start_time
        template.end_time = request.end_time
        template.target_node_ids_raw = _build_target_node_ids_raw(
            request.target_node_ids, expanded_ids
        )
        template.version = (template.version or 0) + 1

        await db.execute(
            delete(InspectionItem).where(InspectionItem.template_id == template.id)
        )

        for major in request.major_items:
            group_item = InspectionItem(
                tenant_id=current_user.tenant_id,
                template_id=template.id,
                parent_item_id=None,
                item_type=ItemType.GROUP,
                sort_order=major.sort_order,
                content=major.title,
                is_active=True,
            )
            db.add(group_item)
            await db.flush()
            for minor in major.minor_items:
                db.add(
                    InspectionItem(
                        tenant_id=current_user.tenant_id,
                        template_id=template.id,
                        parent_item_id=group_item.id,
                        item_type=ItemType.ITEM,
                        sort_order=minor.sort_order,
                        content=minor.content,
                        issue_type=minor.issue_type,
                        total_score=minor.total_score,
                        scoring_options=minor.scoring_options,
                        associated_camera_ids=minor.associated_camera_ids,
                        is_active=True,
                    )
                )

        await db.commit()
        await db.refresh(template)
        return template

    @staticmethod
    async def update_template_status(
        db: AsyncSession,
        tenant_id: int,
        template_id: int,
        inspection_type: InspectionType,
        is_active: bool,
    ) -> InspectionTemplate:
        template = await InspectionTemplateService.get_template(
            db, tenant_id, template_id, inspection_type
        )
        template.is_active = is_active
        await db.commit()
        await db.refresh(template)
        return template

    @staticmethod
    async def delete_template(
        db: AsyncSession,
        tenant_id_or_template_id,
        template_id_or_inspection_type,
        inspection_type: Optional[InspectionType] = None,
    ) -> None:
        if isinstance(template_id_or_inspection_type, InspectionType):
            template = await InspectionTemplateService.get_template(
                db,
                int(tenant_id_or_template_id),
                template_id_or_inspection_type,
            )
        else:
            template = await InspectionTemplateService.get_template(
                db,
                int(tenant_id_or_template_id),
                int(template_id_or_inspection_type),
                inspection_type,
            )
        await db.delete(template)
        await db.commit()

    @staticmethod
    def audit_task(
        db: Session,
        task_id: int,
        approved: bool,
        audit_opinion: Optional[str] = None
    ) -> InspectionTask:
        task = InspectionService.get_task_by_id_sync(db, task_id)
        if not task:
            _raise_http_error(
                status.HTTP_404_NOT_FOUND,
                40400,
                f"巡检任务 {task_id} 不存在",
            )

        target_state = (
            InspectionTaskStatus.COMPLETED if approved
            else InspectionTaskStatus.REJECTED
        )

        validate_state_transition(
            current_state=task.status,
            target_state=target_state
        )

        task.status = target_state
        task.last_audit_opinion = audit_opinion
        task.last_audit_time = _utc_now()

        if approved:
            task.completed_time = _utc_now()

        db.commit()
        db.refresh(task)
        return task