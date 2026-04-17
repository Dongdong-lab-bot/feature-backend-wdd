"""ORM-level tenant isolation guard using do_orm_execute hook."""

from sqlalchemy import event
from sqlalchemy.orm import Session, with_loader_criteria

from app.core.context import system_mode_var, tenant_var
from app.db.base import TenantMixin


@event.listens_for(Session, "do_orm_execute")
def add_tenant_filter(orm_execute_state):
    """Inject tenant filter for all ORM SELECTs unless system mode is enabled.

    - In system mode, skip to allow cross-tenant operations (explicitly controlled).
    - If no tenant and not system mode, block SELECT to prevent data leakage.
    - For other statements (INSERT/UPDATE/DELETE), allow through; rely on app logic for tenant assignment.
    """

    # Relationship loads will inherit criteria from parent queries; no need to re-apply.
    if orm_execute_state.is_relationship_load:
        return

    if system_mode_var.get() is True:
        return

    tenant_id = tenant_var.get()

    if orm_execute_state.is_select:
        if tenant_id is None:
            raise RuntimeError("Missing tenant context")

        orm_execute_state.statement = orm_execute_state.statement.options(
            with_loader_criteria(
                TenantMixin,
                lambda cls: cls.tenant_id == str(tenant_id),
                include_aliases=True,
            )
        )