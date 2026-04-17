"""add device and device record tables

Revision ID: 20260325_add_device_and_device_record_tables
Revises: 20260325_add_user_image_fields
Create Date: 2026-03-25 16:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260325_add_device_and_device_record_tables"
down_revision: Union[str, Sequence[str], None] = "20260325_add_user_image_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "biz_device",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("device_name", sa.String(length=128), nullable=False),
        sa.Column("device_code", sa.String(length=64), nullable=False),
        sa.Column("device_type", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="OFFLINE"),
        sa.Column("last_heartbeat", sa.DateTime(timezone=True), nullable=True),
        sa.Column("extra", sa.JSON(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["org_id"], ["orgs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "device_code", name="uq_biz_device_tenant_code"),
    )
    op.create_index("ix_biz_device_tenant_org", "biz_device", ["tenant_id", "org_id"], unique=False)
    op.create_index("ix_biz_device_tenant_status", "biz_device", ["tenant_id", "status"], unique=False)
    op.create_index("ix_biz_device_tenant_deleted", "biz_device", ["tenant_id", "is_deleted"], unique=False)

    op.create_table(
        "biz_device_record",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("data_type", sa.String(length=64), nullable=False),
        sa.Column("is_related_ledger", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("submit_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["device_id"], ["biz_device.id"]),
        sa.ForeignKeyConstraint(["org_id"], ["orgs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_device_record_tenant_submit", "biz_device_record", ["tenant_id", "submit_date"], unique=False
    )
    op.create_index(
        "ix_device_record_tenant_org_submit",
        "biz_device_record",
        ["tenant_id", "org_id", "submit_date"],
        unique=False,
    )
    op.create_index(
        "ix_device_record_tenant_deleted", "biz_device_record", ["tenant_id", "is_deleted"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_device_record_tenant_deleted", table_name="biz_device_record")
    op.drop_index("ix_device_record_tenant_org_submit", table_name="biz_device_record")
    op.drop_index("ix_device_record_tenant_submit", table_name="biz_device_record")
    op.drop_table("biz_device_record")

    op.drop_index("ix_biz_device_tenant_deleted", table_name="biz_device")
    op.drop_index("ix_biz_device_tenant_status", table_name="biz_device")
    op.drop_index("ix_biz_device_tenant_org", table_name="biz_device")
    op.drop_table("biz_device")
