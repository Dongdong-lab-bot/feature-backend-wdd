"""add user image fields

Revision ID: 20260325_add_user_image_fields
Revises: 20260319_add_video_inspection_fields
Create Date: 2026-03-25 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260325_add_user_image_fields"
down_revision: Union[str, Sequence[str], None] = "20260319_add_video_inspection_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("face_image_url", sa.String(512), nullable=True))
        batch_op.add_column(sa.Column("health_image_url", sa.String(512), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("health_image_url")
        batch_op.drop_column("face_image_url")