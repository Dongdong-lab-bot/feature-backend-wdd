"""组织树租户隔离测试，确保 CTE 查询不会跨租户返回数据。"""

from __future__ import annotations

import pathlib
import sys

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# 确保在仓库根目录运行 pytest 时可以导入 backend 包
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from app.core.context import UserContext  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.tenant_interceptor import TenantSession  # noqa: E402
from app.modules.user.models import Org, Tenant  # noqa: E402
from app.modules.user.service import get_org_tree_recursive  # noqa: E402


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
    session.add(Tenant(id=tenant_id, name=f"租户-{tenant_id}", status="ACTIVE"))
    await session.flush()


async def create_org_tree(session: TenantSession, tenant_id: int, root_name: str) -> Org:
    """为指定租户创建组织树。"""
    login(tenant_id)
    await ensure_tenant(session, tenant_id)
    
    # 创建根节点
    root = Org(
        name=root_name,
        org_type="AREA",
        parent_id=None,
        tenant_id=tenant_id
    )
    session.add(root)
    await session.flush()
    
    # 创建子节点
    child1 = Org(
        name=f"{root_name}-子节点1",
        org_type="AREA",
        parent_id=root.id,
        tenant_id=tenant_id
    )
    session.add(child1)
    
    child2 = Org(
        name=f"{root_name}-子节点2",
        org_type="CANTEEN",
        parent_id=root.id,
        tenant_id=tenant_id
    )
    session.add(child2)
    
    # 创建孙节点
    grandchild = Org(
        name=f"{root_name}-孙节点",
        org_type="CANTEEN",
        parent_id=child1.id,
        tenant_id=tenant_id
    )
    session.add(grandchild)
    
    await session.commit()
    await session.refresh(root)
    return root


async def test_org_tree_tenant_isolation(session):
    """测试组织树查询时的租户隔离。"""
    # 为租户1创建组织树
    root1 = await create_org_tree(session, tenant_id=1, root_name="租户1根节点")
    
    # 为租户2创建组织树
    root2 = await create_org_tree(session, tenant_id=2, root_name="租户2根节点")
    
    # 验证租户1只能看到自己的组织树
    login(tenant_id=1)
    tree1 = await get_org_tree_recursive(session, root1.id, tenant_id=1)
    assert tree1 is not None
    assert tree1.name == "租户1根节点"
    assert len(tree1.children) == 2
    
    # 验证租户2只能看到自己的组织树
    login(tenant_id=2)
    tree2 = await get_org_tree_recursive(session, root2.id, tenant_id=2)
    assert tree2 is not None
    assert tree2.name == "租户2根节点"
    assert len(tree2.children) == 2
    
    # 验证租户1无法访问租户2的组织树
    login(tenant_id=1)
    tree1_access_2 = await get_org_tree_recursive(session, root2.id, tenant_id=1)
    assert tree1_access_2 is None
    
    # 验证租户2无法访问租户1的组织树
    login(tenant_id=2)
    tree2_access_1 = await get_org_tree_recursive(session, root1.id, tenant_id=2)
    assert tree2_access_1 is None


async def test_org_tree_cte_tenant_safety(session):
    """测试 CTE 查询的租户安全性。"""
    # 为租户1创建组织树
    root1 = await create_org_tree(session, tenant_id=1, root_name="租户1根节点")
    
    # 为租户2创建组织树
    root2 = await create_org_tree(session, tenant_id=2, root_name="租户2根节点")
    
    # 验证租户1查询时只返回自己的组织数据
    login(tenant_id=1)
    tree1 = await get_org_tree_recursive(session, root1.id, tenant_id=1)
    assert tree1 is not None
    
    # 遍历树结构，确保所有节点都属于租户1
    def check_tenant_id(node, expected_tenant_id):
        # 由于 OrgResponse 不包含 tenant_id，我们通过名称来验证
        assert "租户1" in node.name
        for child in node.children:
            check_tenant_id(child, expected_tenant_id)
    
    check_tenant_id(tree1, 1)
    
    # 验证租户2查询时只返回自己的组织数据
    login(tenant_id=2)
    tree2 = await get_org_tree_recursive(session, root2.id, tenant_id=2)
    assert tree2 is not None
    
    def check_tenant_id_2(node, expected_tenant_id):
        assert "租户2" in node.name
        for child in node.children:
            check_tenant_id_2(child, expected_tenant_id)
    
    check_tenant_id_2(tree2, 2)
