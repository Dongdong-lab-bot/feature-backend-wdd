"""add ledger instance daily unique constraint

Revision ID: 20260224_add_ledger_instance_daily_unique
Revises: 20260214_add_ledger_module
Create Date: 2026-02-24
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260224_add_ledger_instance_daily_unique"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("biz_ledger_instance") as batch_op:
            batch_op.create_unique_constraint(
                "uq_ledger_instance_daily",
                ["tenant_id", "canteen_id", "template_id", "create_date"],
            )
        return

    op.create_unique_constraint(
        "uq_ledger_instance_daily",
        "biz_ledger_instance",
        ["tenant_id", "canteen_id", "template_id", "create_date"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("biz_ledger_instance") as batch_op:
            batch_op.drop_constraint("uq_ledger_instance_daily", type_="unique")
        return

    op.drop_constraint("uq_ledger_instance_daily", "biz_ledger_instance", type_="unique")
