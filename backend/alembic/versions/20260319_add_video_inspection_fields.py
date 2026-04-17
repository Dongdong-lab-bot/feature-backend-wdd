"""add video inspection fields

Revision ID: 20260319_add_video_inspection_fields
Revises: 9b8d7c6e5f4a
Create Date: 2026-03-19 18:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260319_add_video_inspection_fields"
down_revision: Union[str, Sequence[str], None] = "9b8d7c6e5f4a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("biz_inspection_item") as batch_op:
        batch_op.add_column(sa.Column("associated_camera_ids", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("biz_inspection_item") as batch_op:
        batch_op.drop_column("associated_camera_ids")
