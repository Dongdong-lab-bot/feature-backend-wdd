from datetime import datetime, timezone
from typing import Optional, Dict

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import system_mode_scope
from app.core.deps import get_current_user
from app.core.events import TENANT_CREATED, publish
from app.db import get_db
from app.modules.user.models import Org as OrgModel, Tenant as TenantModel, User as UserModel
from app.modules.user.schemas import OrgAdminCreate, OrgAdminUpdate, TenantCreate

router = APIRouter()


def _ok(data=None, msg: str = "success", code: int = 200):
    return {"code": code, "msg": msg, "data": data}


def _org_to_dict(o: OrgModel, children=None) -> dict:
    return {
        "id": o.id,
        "name": o.name,
        "type": o.org_type,
        "parentId": o.parent_id,
        "children": children or [],
    }


def _build_tree(orgs: list) -> list:
    """将扁平列表构建为树形结构。"""
    nodes: Dict[int, dict] = {o.id: _org_to_dict(o) for o in orgs}
    roots = []
    for o in orgs:
        node = nodes[o.id]
        if o.parent_id and o.parent_id in nodes:
            nodes[o.parent_id]["children"].append(node)
        else:
            roots.append(node)
    return roots


@router.get("/org/tree")
async def get_org_tree(
    type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """获取当前租户下的完整组织树（真实数据库）。"""
    stmt = select(OrgModel)
    if type:
        stmt = stmt.where(OrgModel.org_type == type.upper())

    orgs = (await db.execute(stmt)).scalars().all()
    tree = _build_tree(list(orgs))
    return JSONResponse(status_code=200, content=_ok(data={"tree": tree}))


@router.get("/org/{org_id}")
async def get_org_detail(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """获取单个组织详情。"""
    org = (await db.execute(
        select(OrgModel).where(OrgModel.id == org_id)
    )).scalar_one_or_none()
    if not org:
        return JSONResponse(status_code=404, content=_ok(msg="org not found", code=404))
    return JSONResponse(status_code=200, content=_ok(data=_org_to_dict(org)))


@router.post("/tenant")
async def create_tenant(
    req: TenantCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建租户（平台级接口）。"""

    with system_mode_scope():
        existing = (
            await db.execute(select(TenantModel).where(TenantModel.name == req.name))
        ).scalar_one_or_none()
        if existing:
            return JSONResponse(status_code=400, content=_ok(msg="tenant already exists", code=400))

        tenant = TenantModel(name=req.name, status=req.status)
        db.add(tenant)
        await db.commit()
        await db.refresh(tenant)

    publish(
        TENANT_CREATED,
        {
            "tenant_id": str(tenant.id),
            "admin_user_id": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    return JSONResponse(
        status_code=200,
        content=_ok(data={"id": tenant.id, "name": tenant.name, "status": tenant.status}),
    )



