from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi_events.handlers.local import local_handler
from fastapi_events.typing import Event

from app.core.context import UserContext
from app.core.events import TENANT_CREATED
from app.db.session import SessionLocal
from app.modules.ledger.service import generate_daily_instances_for_canteens
from app.modules.user.service import get_active_tenant_ids, get_canteen_ids_by_tenant

logger = logging.getLogger(__name__)

_scheduler: Optional[AsyncIOScheduler] = None


async def _run_daily_sop_job() -> None:
    today = date.today()
    async with SessionLocal() as db:
        tenant_ids = await get_active_tenant_ids(db)
        if not tenant_ids:
            return

        for tenant_id in tenant_ids:
            # 为当前租户设置上下文，保证多租户拦截器在需要时能工作
            UserContext.reset()
            UserContext.set_tenant_id(str(tenant_id))

            try:
                canteen_ids = await get_canteen_ids_by_tenant(db, tenant_id)
                if not canteen_ids:
                    continue

                created = await generate_daily_instances_for_canteens(
                    db=db,
                    tenant_id=tenant_id,
                    canteen_ids=canteen_ids,
                    biz_date=today,
                )
                logger.info(
                    "SOP daily job: tenant=%s, biz_date=%s, created_instances=%s",
                    tenant_id,
                    today.isoformat(),
                    created,
                )
            finally:
                UserContext.reset()


def start_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        return

    scheduler = AsyncIOScheduler()
    # 每天早上 8 点跑一次
    scheduler.add_job(
        _run_daily_sop_job,
        trigger="cron",
        hour=8,
        minute=0,
        id="sop_daily_generation",
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info("SOP APScheduler started")


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is None:
        return

    _scheduler.shutdown(wait=False)
    logger.info("SOP APScheduler stopped")
    _scheduler = None


@local_handler.register(event_name=TENANT_CREATED)
async def handle_tenant_created(event: Event) -> None:
    event_name, payload = event
    try:
        tenant_id = int(payload.get("tenant_id"))
    except Exception:
        return

    today = date.today()
    async with SessionLocal() as db:
        UserContext.reset()
        UserContext.set_tenant_id(str(tenant_id))
        try:
            canteen_ids = await get_canteen_ids_by_tenant(db, tenant_id)
            if not canteen_ids:
                return

            created = await generate_daily_instances_for_canteens(
                db=db,
                tenant_id=tenant_id,
                canteen_ids=canteen_ids,
                biz_date=today,
            )
            logger.info(
                "SOP tenant-created job: tenant=%s, biz_date=%s, created_instances=%s",
                tenant_id,
                today.isoformat(),
                created,
            )
        finally:
            UserContext.reset()