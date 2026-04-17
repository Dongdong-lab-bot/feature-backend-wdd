"""Ledger module CRUD operations for async SQLAlchemy.

This module provides async database operations for ledger templates,
including scope management (users and canteens coverage).

该部分按智慧食安平台通用规范实现。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ledger.models import LedgerTemplate, TemplateScope


class TemplateCrud:
    """Template CRUD operations."""

    @staticmethod
    async def get_template_by_id(
        db: AsyncSession,
        template_id: int,
        tenant_id: int,
    ) -> Optional[LedgerTemplate]:
        """Get template by ID with tenant isolation."""
        stmt = select(LedgerTemplate).where(
            LedgerTemplate.id == template_id,
            LedgerTemplate.tenant_id == tenant_id,
            LedgerTemplate.is_deleted == False,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_template_scope(
        db: AsyncSession,
        template_id: int,
        tenant_id: int,
        scope_data: Dict[str, Any],
    ) -> bool:
        """Update template scope (users/canteens)."""
        stmt = (
            update(LedgerTemplate)
            .where(
                LedgerTemplate.id == template_id,
                LedgerTemplate.tenant_id == tenant_id,
            )
            .values(scope=scope_data)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0


class TemplateScopeCrud:
    """Template scope CRUD operations for managing user/canteen coverage."""

    @staticmethod
    async def get_scope_by_template_id(
        db: AsyncSession,
        template_id: int,
        tenant_id: int,
    ) -> Optional[TemplateScope]:
        """Get scope by template ID with tenant isolation."""
        stmt = select(TemplateScope).where(
            TemplateScope.template_id == template_id,
            TemplateScope.tenant_id == tenant_id,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_scope(
        db: AsyncSession,
        template_id: int,
        tenant_id: int,
        user_ids: List[int],
        canteen_ids: List[int],
    ) -> TemplateScope:
        """Create new scope for template."""
        scope = TemplateScope(
            template_id=template_id,
            tenant_id=tenant_id,
            user_ids=user_ids,
            canteen_ids=canteen_ids,
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
    ) -> bool:
        """Batch update scope users."""
        scope = await TemplateScopeCrud.get_scope_by_template_id(db, template_id, tenant_id)
        if scope:
            scope.user_ids = user_ids
            await db.commit()
            return True
        else:
            await TemplateScopeCrud.create_scope(db, template_id, tenant_id, user_ids, [])
            return True

    @staticmethod
    async def update_scope_canteens(
        db: AsyncSession,
        template_id: int,
        tenant_id: int,
        canteen_ids: List[int],
    ) -> bool:
        """Batch update scope canteens."""
        scope = await TemplateScopeCrud.get_scope_by_template_id(db, template_id, tenant_id)
        if scope:
            scope.canteen_ids = canteen_ids
            await db.commit()
            return True
        else:
            await TemplateScopeCrud.create_scope(db, template_id, tenant_id, [], canteen_ids)
            return True

    @staticmethod
    async def delete_scope(
        db: AsyncSession,
        template_id: int,
        tenant_id: int,
    ) -> bool:
        """Delete scope for template."""
        scope = await TemplateScopeCrud.get_scope_by_template_id(db, template_id, tenant_id)
        if scope:
            await db.delete(scope)
            await db.commit()
            return True
        return False
