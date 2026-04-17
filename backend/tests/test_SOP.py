from __future__ import annotations

import pathlib
import sys
from datetime import date

import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from app.core.context import UserContext  # noqa: E402
from app.core.events import TENANT_CREATED  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.tenant_interceptor import TenantSession  # noqa: E402
from app.modules.ledger.models import LedgerInstance, LedgerTask, LedgerTemplate  # noqa: E402
from app.modules.user.models import Org, Tenant  # noqa: E402

import app.modules.ledger.scheduler as scheduler  # noqa: E402


pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture()
async def session_local():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(
        bind=engine,
        class_=TenantSession,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        future=True,
    )

    scheduler.SessionLocal = SessionLocal

    try:
        yield SessionLocal
    finally:
        UserContext.reset()
        await engine.dispose()


async def _seed_tenant_with_canteen_and_task(SessionLocal, tenant_id: int) -> None:
    async with SessionLocal() as db:
        if await db.get(Tenant, tenant_id) is None:
            db.add(Tenant(id=tenant_id, name=f"tenant-{tenant_id}", status="ACTIVE"))
            await db.commit()

        UserContext.reset()
        UserContext.set_tenant_id(str(tenant_id))

        org = Org(name=f"canteen-{tenant_id}-1", org_type="CANTEEN", parent_id=None)
        db.add(org)

        tpl = LedgerTemplate(
            title=f"tpl-{tenant_id}",
            description=None,
            schema={"fields": [{"field_id": "f1", "type": "string", "required": True}]},
            hash=None,
            is_deleted=False,
            is_active=True,
        )
        db.add(tpl)
        await db.flush()

        task = LedgerTask(
            name=f"task-{tenant_id}",
            template_id=tpl.id,
            cron="0 8 * * *",
            target_config={},
            is_active=True,
        )
        db.add(task)
        await db.commit()
        UserContext.reset()


async def _count_instances(SessionLocal, tenant_id: int) -> int:
    async with SessionLocal() as db:
        UserContext.reset()
        UserContext.set_tenant_id(str(tenant_id))
        n = (await db.execute(select(func.count(LedgerInstance.id)))).scalar_one()
        UserContext.reset()
        return int(n)


async def test_sop_daily_job_generates_once_per_day(session_local):
    SessionLocal = session_local
    await _seed_tenant_with_canteen_and_task(SessionLocal, 1001)

    before = await _count_instances(SessionLocal, 1001)
    await scheduler._run_daily_sop_job()
    after1 = await _count_instances(SessionLocal, 1001)
    await scheduler._run_daily_sop_job()
    after2 = await _count_instances(SessionLocal, 1001)

    assert before == 0
    assert after1 == 1
    assert after2 == 1


async def test_sop_tenant_created_event_generates_today(session_local):
    SessionLocal = session_local
    await _seed_tenant_with_canteen_and_task(SessionLocal, 1002)

    await scheduler.handle_tenant_created((TENANT_CREATED, {"tenant_id": "1002"}))

    assert await _count_instances(SessionLocal, 1002) == 1