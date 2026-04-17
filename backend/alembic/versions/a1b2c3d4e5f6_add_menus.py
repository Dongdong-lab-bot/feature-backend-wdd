from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "56c170054082"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "menus",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("menus.id"), nullable=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("path", sa.String(length=256), nullable=False, server_default=""),
        sa.Column("component", sa.String(length=256), nullable=False, server_default=""),
        sa.Column("sort", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("hidden", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_menu_parent", "menus", ["parent_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_menu_parent", table_name="menus")
    op.drop_table("menus")
