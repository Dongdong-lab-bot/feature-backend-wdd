"""自动执行多租户隔离策略的 SQLAlchemy 会话实现。"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Sequence

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.sql.dml import Delete, Insert, Update
from sqlalchemy.sql.selectable import Select

from app.core.context import TenantContextMissing, UserContext
from app.db.mixins import TENANT_AWARE_MODELS, TenantMixin


class TenantAccessError(RuntimeError):
    """当代码试图访问非本租户数据时抛出。"""


class TenantSession(AsyncSession):
    """在 ORM 层自动注入租户过滤条件的 Session。"""


def _inject_tenant_param(params: Dict[str, Any], tenant_id: int) -> Dict[str, Any]:
    if "tenant_id" not in params or params["tenant_id"] is None:
        params["tenant_id"] = tenant_id
    elif params["tenant_id"] != tenant_id:
        raise TenantAccessError("禁止以当前租户之外的 tenant_id 执行操作。")
    return params


@event.listens_for(Session, "before_flush")
def _before_flush(session: Session, flush_context, instances) -> None:
    try:
        tenant_id = UserContext.require_tenant_id_int()
    except TenantContextMissing:
        if UserContext.is_system_mode():
            return
        raise TenantAccessError("缺少租户上下文，禁止写入租户数据。")

    def guard(obj: Any) -> None:
        if isinstance(obj, TenantMixin):
            current = getattr(obj, "tenant_id", None)
            if current is None:
                setattr(obj, "tenant_id", tenant_id)
            elif current != tenant_id:
                raise TenantAccessError("检测到跨租户写入，已拒绝该操作。")

    for obj in session.new:
        guard(obj)
    for obj in session.dirty:
        guard(obj)
    for obj in session.deleted:
        guard(obj)


@event.listens_for(Session, "do_orm_execute")
def _add_tenant_guards(execute_state):
    try:
        tenant_id = UserContext.require_tenant_id_int()
    except TenantContextMissing:
        if UserContext.is_system_mode():
            return
        raise TenantAccessError("缺少租户上下文，禁止访问租户数据。")

    statement = execute_state.statement

    if isinstance(statement, Select):
        # 针对 SELECT 语句逐一限制最终参与查询的表
        for from_clause in statement.get_final_froms():
            if hasattr(from_clause, "c") and "tenant_id" in from_clause.c:
                statement = statement.where(from_clause.c.tenant_id == tenant_id)

        execute_state.statement = statement
    elif isinstance(statement, (Update, Delete)):
        table = statement.table
        if "tenant_id" in table.c:
            execute_state.statement = statement.where(table.c.tenant_id == tenant_id)
    elif isinstance(statement, Insert):
        table = statement.table
        if "tenant_id" not in table.c:
            return
        params = execute_state.parameters
        if params is None:
            execute_state.parameters = {"tenant_id": tenant_id}
        elif isinstance(params, (list, tuple)):
            # SQLAlchemy 在此处将元素视作 Any，显式转换需要忽略类型告警
            execute_state.parameters = [
                _inject_tenant_param(dict(p), tenant_id) for p in params  # type: ignore[arg-type]
            ]
        elif isinstance(params, dict):
            execute_state.parameters = _inject_tenant_param(params, tenant_id)


__all__ = ["TenantSession", "TenantAccessError"]
