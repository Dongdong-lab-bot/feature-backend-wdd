"""add api_key to biz_device for device authentication

Revision ID: 20260329_add_api_key_to_biz_device
Revises: 20260326_extend_device_for_morning_check
Create Date: 2026-03-29 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260329_add_api_key_to_biz_device"
down_revision: Union[str, Sequence[str], None] = "20260326_extend_device_for_morning_check"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("biz_device", sa.Column("api_key", sa.String(length=64), nullable=True))
    op.create_unique_constraint("uq_biz_device_api_key", "biz_device", ["api_key"])


def downgrade() -> None:
    op.drop_constraint("uq_biz_device_api_key", "biz_device", type_="unique")
    op.drop_column("biz_device", "api_key")
