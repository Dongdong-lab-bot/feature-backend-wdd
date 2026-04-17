from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9b8d7c6e5f4a"
down_revision: Union[str, Sequence[str], None] = "311c79a160f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), nullable=False, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("app_client", sa.String(length=32), nullable=False),
        sa.Column("jti", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("jti", name="uq_refresh_token_jti"),
    )
    op.create_index("ix_refresh_token_user", "refresh_tokens", ["user_id"], unique=False)
    op.create_index("ix_refresh_token_tenant", "refresh_tokens", ["tenant_id"], unique=False)
    op.create_index("ix_refresh_token_app_client", "refresh_tokens", ["app_client"], unique=False)
    op.create_index(
        "ix_refresh_token_valid_lookup",
        "refresh_tokens",
        ["user_id", "revoked_at", "expires_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_refresh_token_valid_lookup", table_name="refresh_tokens")
    op.drop_index("ix_refresh_token_app_client", table_name="refresh_tokens")
    op.drop_index("ix_refresh_token_tenant", table_name="refresh_tokens")
    op.drop_index("ix_refresh_token_user", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
