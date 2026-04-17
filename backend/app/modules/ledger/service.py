"""Ledger module services: task generation + form pipeline helpers."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.context import UserContext
from app.modules.ledger.constants import ALLOWED_TRANSITIONS, LedgerStatus
from app.modules.ledger.context import build_auto_fill_context
from app.modules.ledger.form_engine import auto_fill, validate_data
from app.modules.ledger.models import ExportLog, LedgerInstance, LedgerTask, LedgerTemplate, SOPTask, TemplateScope
from app.modules.ledger.security import calculate_security_hash
from app.modules.user.models import Org, User


SALT = "food_safety_platform_salt"


async def generate_daily_instances_for_canteens(
    db: AsyncSession,
    tenant_id: int,
    canteen_ids: Iterable[int],
    biz_date: date,
) -> int:
    """Generate pending instances for each canteen based on active tasks."""

    canteen_ids = list(dict.fromkeys(canteen_ids))
    if not canteen_ids:
        return 0

    start_dt = datetime(biz_date.year, biz_date.month, biz_date.day)
    end_dt = start_dt + timedelta(days=1)

    tasks_result = await db.execute(
        select(LedgerTask).where(
            LedgerTask.tenant_id == tenant_id,
            LedgerTask.is_active.is_(True),
        )
    )
    tasks = sorted(list(tasks_result.scalars()), key=lambda task: task.id)
    if not tasks:
        return 0

    seen_template_ids: set[int] = set()
    unique_tasks: list[LedgerTask] = []
    for task in tasks:
        if task.template_id in seen_template_ids:
            continue
        seen_template_ids.add(task.template_id)
        unique_tasks.append(task)
    tasks = unique_tasks

    created_count = 0

    for task in tasks:
        template = await db.get(LedgerTemplate, task.template_id)
        if template is None:
            continue

        for canteen_id in canteen_ids:
            exists_stmt = (
                select(LedgerInstance.id)
                .where(
                    LedgerInstance.tenant_id == tenant_id,
                    LedgerInstance.template_id == task.template_id,
                    LedgerInstance.canteen_id == canteen_id,
                    LedgerInstance.create_date >= start_dt,
                    LedgerInstance.create_date < end_dt,
                )
                .limit(1)
            )
            exists_result = await db.execute(exists_stmt)
            if exists_result.first() is not None:
                continue

            instance = LedgerInstance(
                tenant_id=tenant_id,
                template_id=task.template_id,
                task_id=task.id,
                canteen_id=canteen_id,
                status=LedgerStatus.PENDING,
                schema_snapshot=template.schema or {},
                content={},
                create_date=start_dt,
            )
            db.add(instance)
            created_count += 1

    if created_count:
        await db.commit()

    return created_count


class LedgerService:
    """台账核心业务逻辑（同步 + 异步入口）。"""

    @staticmethod
    def _build_form_context(db: Session, ledger: LedgerInstance) -> dict:
        """聚合自动填充所需的上下文信息。"""

        canteen = db.query(Org).filter(Org.id == ledger.canteen_id).first()
        canteen_name = canteen.name if canteen else ""

        user_name = ""
        user_id = UserContext.get_user_id()
        if user_id:
            try:
                user_id_int = int(user_id)
            except ValueError:
                user_id_int = None
            if user_id_int is not None:
                user = db.query(User).filter(User.id == user_id_int).first()
                if user:
                    user_name = user.real_name or user.username

        return build_auto_fill_context(canteen_name=canteen_name, user_name=user_name)

    @classmethod
    def prepare_form_content(cls, db: Session, ledger: LedgerInstance, content: dict) -> dict:
        """集中处理表单校验与自动填充，供提交/暂存复用。"""

        validate_data(ledger.schema_snapshot, content)
        context = cls._build_form_context(db, ledger)
        return auto_fill(ledger.schema_snapshot, content, context)

    @staticmethod
    def get_ledger(db: Session, ledger_id: int) -> LedgerInstance:
        ledger = db.query(LedgerInstance).filter(LedgerInstance.id == ledger_id).first()
        if not ledger:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="台账不存在")
        return ledger

    @staticmethod
    def validate_state_transition(current_status: LedgerStatus, new_status: LedgerStatus) -> bool:
        if new_status not in ALLOWED_TRANSITIONS.get(current_status, []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid state transition from {current_status} to {new_status}",
            )
        return True

    @staticmethod
    def submit_ledger(db: Session, ledger_id: int, content: dict) -> LedgerInstance:
        ledger = LedgerService.get_ledger(db, ledger_id)

        if ledger.status == LedgerStatus.SIGNED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="已签名台账无法修改")

        filled_content = LedgerService.prepare_form_content(db, ledger, content)

        ledger.content = filled_content
        LedgerService.validate_state_transition(ledger.status, LedgerStatus.SIGNED)
        ledger.status = LedgerStatus.SIGNED

        security_hash = calculate_security_hash(filled_content, ledger.schema_snapshot, SALT)
        ledger.security_hash = security_hash
        ledger.submit_time = datetime.now(timezone.utc)

        db.commit()
        db.refresh(ledger)
        return ledger

    @staticmethod
    def verify_ledger(db: Session, ledger_id: int) -> bool:
        ledger = LedgerService.get_ledger(db, ledger_id)
        current_hash = calculate_security_hash(ledger.content, ledger.schema_snapshot, SALT)
        return current_hash == ledger.security_hash

    @staticmethod
    def archive_ledger(db: Session, ledger_id: int) -> LedgerInstance:
        ledger = LedgerService.get_ledger(db, ledger_id)
        LedgerService.validate_state_transition(ledger.status, LedgerStatus.ARCHIVED)
        ledger.status = LedgerStatus.ARCHIVED
        db.commit()
        db.refresh(ledger)
        return ledger

    @staticmethod
    async def create_instance_from_template(
        db: AsyncSession,
        template_id: int,
        canteen_id: int,
        tenant_id: int,
    ) -> LedgerInstance:
        """Create a ledger instance for the given template if one does not exist."""

        biz_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        existing_stmt = select(LedgerInstance).where(
            LedgerInstance.tenant_id == tenant_id,
            LedgerInstance.canteen_id == canteen_id,
            LedgerInstance.template_id == template_id,
            LedgerInstance.create_date == biz_date,
        )
        existing = await db.scalar(existing_stmt)
        if existing:
            return existing

        template = await db.get(LedgerTemplate, template_id)
        if not template:
            raise ValueError("Template not found")

        snapshot_data = template.schema.copy() if template.schema else {}

        instance = LedgerInstance(
            template_id=template.id,
            canteen_id=canteen_id,
            tenant_id=tenant_id,
            create_date=biz_date,
            status=LedgerStatus.PENDING,
            schema_snapshot=snapshot_data,
            content={},
        )

        db.add(instance)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            existed_after_race = await db.scalar(existing_stmt)
            if existed_after_race:
                return existed_after_race
            raise
        await db.refresh(instance)
        return instance


class TemplateService:
    @staticmethod
    def get_templates(db: Session, page: int = 1, size: int = 10) -> dict:
        query = db.query(LedgerTemplate)
        total = query.count()
        templates = query.offset((page - 1) * size).limit(size).all()
        return {"total": total, "page": page, "size": size, "records": templates}

    @staticmethod
    def create_template(db: Session, template_data: dict) -> LedgerTemplate:
        template = LedgerTemplate(**template_data)
        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    @staticmethod
    def update_template(db: Session, template_id: int, template_data: dict) -> LedgerTemplate:
        template = db.query(LedgerTemplate).filter(LedgerTemplate.id == template_id).first()
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模板不存在")
        for key, value in template_data.items():
            setattr(template, key, value)
        db.commit()
        db.refresh(template)
        return template

    @staticmethod
    def delete_template(db: Session, template_id: int) -> bool:
        template = db.query(LedgerTemplate).filter(LedgerTemplate.id == template_id).first()
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模板不存在")
        db.delete(template)
        db.commit()
        return True


class SOPTaskService:
    @staticmethod
    def create_task(db: Session, task_data: dict) -> SOPTask:
        task = SOPTask(**task_data)
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def update_task_status(db: Session, task_id: int, is_active: int) -> SOPTask:
        task = db.query(SOPTask).filter(SOPTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
        task.is_active = is_active
        db.commit()
        db.refresh(task)
        return task


COMPLETED_STATUSES = (
    LedgerStatus.SIGNED,
    LedgerStatus.ARCHIVED,
)


def _calc_rate(total: int, completed: int) -> float:
    if total <= 0:
        return 0.0
    return round(completed / total, 2)


async def get_completion_stats(
    db: AsyncSession,
    tenant_id: int,
    biz_date: date,
    canteen_id: Optional[int] = None,
) -> Dict[str, Any]:
    stmt = (
        select(
            LedgerInstance.canteen_id.label("canteen_id"),
            func.count(LedgerInstance.id).label("total"),
            func.sum(
                case(
                    (LedgerInstance.status.in_(COMPLETED_STATUSES), 1),
                    else_=0,
                )
            ).label("completed"),
        )
        .where(
            LedgerInstance.tenant_id == tenant_id,
            func.date(LedgerInstance.create_date) == biz_date,
        )
        .group_by(LedgerInstance.canteen_id)
    )

    if canteen_id is not None:
        stmt = stmt.where(LedgerInstance.canteen_id == canteen_id)

    result = await db.execute(stmt)
    rows = result.all()

    items: List[Dict[str, Any]] = []
    total_all = 0
    completed_all = 0

    for row in rows:
        row_total = int(row.total or 0)
        row_completed = int(row.completed or 0)
        total_all += row_total
        completed_all += row_completed
        items.append(
            {
                "canteen_id": row.canteen_id,
                "total": row_total,
                "completed": row_completed,
                "rate": _calc_rate(row_total, row_completed),
            }
        )

    rate_all = _calc_rate(total_all, completed_all)

    return {
        "date": biz_date.isoformat(),
        "total": total_all,
        "completed": completed_all,
        "rate": rate_all,
        "items": items,
    }


class ReportService:
    """报表导出相关的同步/异步数据库操作封装。"""

    @staticmethod
    def _build_export_log(
        *,
        user_id: str,
        tenant_id: str,
        export_date: str,
        template_id: Optional[int],
        canteen_id: Optional[str],
        format: str,
        record_count: int,
        ip_address: Optional[str],
        user_agent: Optional[str],
    ) -> ExportLog:
        return ExportLog(
            user_id=user_id,
            tenant_id=tenant_id,
            export_date=export_date,
            template_id=template_id,
            canteen_id=canteen_id,
            format=format,
            record_count=record_count,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @classmethod
    def record_export_log(
        cls,
        db: Session,
        *,
        user_id: str,
        tenant_id: str,
        export_date: str,
        template_id: Optional[int],
        canteen_id: Optional[str],
        format: str,
        record_count: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> ExportLog:
        """同步 Session 版本，供现有 FastAPI 依赖与脚本使用。"""

        log = cls._build_export_log(
            user_id=user_id,
            tenant_id=tenant_id,
            export_date=export_date,
            template_id=template_id,
            canteen_id=canteen_id,
            format=format,
            record_count=record_count,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @classmethod
    async def record_export_log_async(
        cls,
        db: AsyncSession,
        *,
        user_id: str,
        tenant_id: str,
        export_date: str,
        template_id: Optional[int],
        canteen_id: Optional[str],
        format: str,
        record_count: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> ExportLog:
        """异步 Session 版本，供 APScheduler/RQ 等异步任务复用。"""

        log = cls._build_export_log(
            user_id=user_id,
            tenant_id=tenant_id,
            export_date=export_date,
            template_id=template_id,
            canteen_id=canteen_id,
            format=format,
            record_count=record_count,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log


class TemplateScopeService:
    """模板覆盖范围服务（异步 SQLAlchemy）。

    该部分按智慧食安平台通用规范实现。
    """

    @staticmethod
    async def get_scope_by_template(
        db: AsyncSession,
        template_id: int,
        tenant_id: int,
    ) -> Optional[TemplateScope]:
        """获取模板覆盖范围。"""
        stmt = select(TemplateScope).where(
            TemplateScope.template_id == template_id,
            TemplateScope.tenant_id == tenant_id,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_or_create_scope(
        db: AsyncSession,
        template_id: int,
        tenant_id: int,
    ) -> TemplateScope:
        """获取或创建模板覆盖范围。"""
        scope = await TemplateScopeService.get_scope_by_template(db, template_id, tenant_id)
        if not scope:
            scope = TemplateScope(
                template_id=template_id,
                tenant_id=tenant_id,
                user_ids=[],
                canteen_ids=[],
            )
            db.add(scope)
            await db.commit()
            await db.refresh(scope)
        return scope

    @staticmethod
    async def update_scope_users(
        db: AsyncSession,
        template_id: int,
        tenant_id: int,
        user_ids: List[int],
    ) -> TemplateScope:
        """批量更新覆盖人员。"""
        scope = await TemplateScopeService.get_or_create_scope(db, template_id, tenant_id)
        scope.user_ids = user_ids
        await db.commit()
        await db.refresh(scope)
        return scope

    @staticmethod
    async def update_scope_canteens(
        db: AsyncSession,
        template_id: int,
        tenant_id: int,
        canteen_ids: List[int],
    ) -> TemplateScope:
        """批量更新覆盖食堂。"""
        scope = await TemplateScopeService.get_or_create_scope(db, template_id, tenant_id)
        scope.canteen_ids = canteen_ids
        await db.commit()
        await db.refresh(scope)
        return scope

    @staticmethod
    async def update_scope_full(
        db: AsyncSession,
        template_id: int,
        tenant_id: int,
        description: Optional[str] = None,
        scope_data: Optional[Dict[str, Any]] = None,
        extra_config: Optional[Dict[str, Any]] = None,
    ) -> Tuple[LedgerTemplate, TemplateScope]:
        """完整更新模板覆盖范围（包含模板自身字段）。

        Returns:
            Tuple of (updated_template, updated_scope)
        """
        template = await db.get(LedgerTemplate, template_id)
        if not template:
            raise ValueError("模板不存在")

        if description is not None:
            template.description = description

        if extra_config is not None:
            scope = await TemplateScopeService.get_or_create_scope(db, template_id, tenant_id)
            scope.extra_config = extra_config

        if scope_data is not None:
            scope = await TemplateScopeService.get_or_create_scope(db, template_id, tenant_id)
            if "users" in scope_data:
                scope.user_ids = scope_data.get("users", [])
            if "canteens" in scope_data:
                scope.canteen_ids = scope_data.get("canteens", [])

        await db.commit()
        await db.refresh(template)

        final_scope = await TemplateScopeService.get_scope_by_template(db, template_id, tenant_id)
        return template, final_scope or TemplateScope(
            template_id=template_id,
            tenant_id=tenant_id,
            user_ids=[],
            canteen_ids=[],
        )
