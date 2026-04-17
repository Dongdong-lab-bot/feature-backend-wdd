"""merge heads only

Revision ID: 20260224_merge_heads_only
Revises: 311c79a160f2, 20260224_add_ledger_instance_daily_unique
Create Date: 2026-02-24
"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "20260224_merge_heads_only"
down_revision: Union[str, Sequence[str], None] = (
    "311c79a160f2",
    "20260224_add_ledger_instance_daily_unique",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
