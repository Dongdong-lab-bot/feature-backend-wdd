from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '311c79a160f2'
down_revision: Union[str, Sequence[str], None] = 'd32dcb70071a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "users" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("users")}
    if "email" in columns:
        return

    op.add_column('users', sa.Column('email', sa.String(length=255), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "users" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("users")}
    if "email" not in columns:
        return

    op.drop_column('users', 'email')
