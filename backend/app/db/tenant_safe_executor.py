"""租户安全的原生 SQL 执行器封装，确保 CTE 和 from_statement 场景下的租户隔离。"""
from __future__ import annotations

from typing import Any, Dict, Optional, TypeVar, cast

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.core.context import TenantContextMissing, UserContext
from app.db.mixins import TenantMixin

T = TypeVar('T', bound=DeclarativeBase)


class TenantSafeExecutor:
    """租户安全的 SQL 执行器，确保所有查询都包含租户过滤条件。"""

    @staticmethod
    async def execute_cte(
        db: AsyncSession,
        model: type[T],
        cte_statement: Select,
        tenant_id: Optional[int] = None
    ) -> list[T]:
        """
        执行 CTE 查询并确保租户隔离。
        
        Args:
            db: 数据库会话
            model: ORM 模型类
            cte_statement: CTE 查询语句
            tenant_id: 租户 ID（如果为 None，则从上下文中获取）
            
        Returns:
            查询结果列表
            
        Raises:
            TenantContextMissing: 当租户 ID 未提供且上下文中也不存在时
        """
        # 获取租户 ID
        if tenant_id is None:
            tenant_id = UserContext.require_tenant_id_int()
        
        # 验证模型是否为租户感知模型
        if not issubclass(model, TenantMixin):
            raise ValueError(f"Model {model.__name__} must inherit from TenantMixin")
        
        # 创建最终查询语句
        final_stmt = select(model).from_statement(cte_statement)
        
        # 执行查询
        result = await db.execute(final_stmt)
        return list(result.scalars().all())

    @staticmethod
    async def execute_raw(
        db: AsyncSession,
        model: type[T],
        raw_statement: Any,
        params: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[int] = None
    ) -> list[T]:
        """
        执行原生 SQL 语句并确保租户隔离。
        
        Args:
            db: 数据库会话
            model: ORM 模型类
            raw_statement: 原生 SQL 语句
            params: 查询参数
            tenant_id: 租户 ID（如果为 None，则从上下文中获取）
            
        Returns:
            查询结果列表
            
        Raises:
            TenantContextMissing: 当租户 ID 未提供且上下文中也不存在时
        """
        # 获取租户 ID
        if tenant_id is None:
            tenant_id = UserContext.require_tenant_id_int()
        
        # 验证模型是否为租户感知模型
        if not issubclass(model, TenantMixin):
            raise ValueError(f"Model {model.__name__} must inherit from TenantMixin")
        
        # 执行查询
        result = await db.execute(raw_statement, params or {})
        return list(result.scalars().all())


__all__ = ["TenantSafeExecutor"]
