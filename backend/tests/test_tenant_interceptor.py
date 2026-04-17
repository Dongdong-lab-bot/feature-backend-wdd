"""多租户拦截器的异步化测试，确保 TenantSession 行为稳定。"""

from __future__ import annotations

import pathlib
import sys

import pytest
import pytest_asyncio
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# 确保在仓库根目录运行 pytest 时可以导入 backend 包
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from app.core.context import UserContext  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.tenant_interceptor import TenantAccessError, TenantSession  # noqa: E402
from app.modules.user.models import Org, Tenant, User  # noqa: E402


pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture()
async def session():
    """为每个测试提供独立的 AsyncSession，模拟真实请求链路。"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(
        bind=engine,
        class_=TenantSession,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        future=True,
    )

    async with Session() as db:
        try:
            yield db
        finally:
            UserContext.reset()

    await engine.dispose()


def login(tenant_id: int, user_id: int = 1) -> None:
    """写入 UserContext，模拟已认证用户。"""
    UserContext.set_tenant_id(str(tenant_id))
    UserContext.set_user_id(str(user_id))
    UserContext.set_role_type("REGULATOR")
    assert UserContext.require_tenant_id_int() == tenant_id


async def ensure_tenant(session: TenantSession, tenant_id: int) -> None:
    """若库中无该租户，则补充一条基础数据，避免外键校验失败。"""
    if await session.get(Tenant, tenant_id):
        return
    session.add(Tenant(id=tenant_id, name=f"租户-{tenant_id}"))
    await session.flush()


async def seed_org(session: TenantSession, tenant_id: int, name: str = "机构") -> Org:
    login(tenant_id)
    await ensure_tenant(session, tenant_id)
    org = Org(name=f"{name}-{tenant_id}", org_type="AREA", parent_id=None)
    session.add(org)
    await session.commit()
    await session.refresh(org)
    return org


async def seed_user(session: TenantSession, tenant_id: int, username: str) -> User:
    """创建测试用户，并确保其组织及租户匹配当前上下文。"""
    org = await seed_org(session, tenant_id)
    login(tenant_id)
    user = User(
        username=username,
        real_name=username.capitalize(),
        password_hash="hashed",
        role_type="REGULATOR",
        org_id=org.id,
        tenant_id=tenant_id,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def test_insert_auto_populates_tenant_id(session):
    org = await seed_org(session, tenant_id=1, name="总部")
    assert org.tenant_id == 1


async def test_select_is_scoped_by_context(session):
    user_a = await seed_user(session, tenant_id=1, username="alice")
    user_b = await seed_user(session, tenant_id=2, username="bob")

    assert user_a.tenant_id == 1
    assert user_b.tenant_id == 2

    login(tenant_id=1)
    rows = await session.execute(select(User.username).order_by(User.username))
    assert rows.scalars().all() == ["alice"]

    login(tenant_id=2)
    fetched = await session.get(User, user_b.id)
    assert fetched and fetched.username == "bob"
    rows = await session.execute(select(User.username).order_by(User.username))
    assert rows.scalars().all() == ["bob"]


async def test_manual_tenant_override_is_rejected(session):
    login(tenant_id=1)
    rogue_org = Org(name="违规机构", org_type="AREA", parent_id=0, tenant_id=999)
    session.add(rogue_org)

    with pytest.raises(TenantAccessError):
        await session.flush()


async def test_bulk_update_only_touches_current_tenant(session):
    user_a = await seed_user(session, tenant_id=1, username="tenant-a")
    user_b = await seed_user(session, tenant_id=2, username="tenant-b")

    login(tenant_id=1)
    await session.execute(update(User).values(real_name="updated"))
    await session.commit()

    login(tenant_id=1)
    refreshed_a = await session.get(User, user_a.id)
    assert refreshed_a and refreshed_a.real_name == "updated"

    login(tenant_id=2)
    refreshed_b = await session.get(User, user_b.id)
    assert refreshed_b and refreshed_b.real_name == user_b.real_name
