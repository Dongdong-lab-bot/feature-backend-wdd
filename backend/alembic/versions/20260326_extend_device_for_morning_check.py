"""extend device fields and record fields for morning check

Revision ID: 20260326_extend_device_for_morning_check
Revises: 20260325_add_device_and_device_record_tables
Create Date: 2026-03-26 10:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260326_extend_device_for_morning_check"
down_revision: Union[str, Sequence[str], None] = "20260325_add_device_and_device_record_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("biz_device", sa.Column("vendor", sa.String(length=64), nullable=True))
    op.add_column("biz_device", sa.Column("model", sa.String(length=64), nullable=True))
    op.add_column("biz_device", sa.Column("installed_at", sa.DateTime(timezone=True), nullable=True))

    op.add_column("biz_device_record", sa.Column("detail_json", sa.JSON(), nullable=True))
    op.add_column(
        "biz_device_record",
        sa.Column("source", sa.String(length=32), nullable=False, server_default="DEVICE_AUTO"),
    )
    op.add_column("biz_device_record", sa.Column("trace_id", sa.String(length=64), nullable=True))
    op.add_column(
        "biz_device_record",
        sa.Column("process_result", sa.String(length=32), nullable=False, server_default="SUCCESS"),
    )

    op.create_index(
        "ix_device_record_tenant_type_submit",
        "biz_device_record",
        ["tenant_id", "data_type", "submit_date"],
        unique=False,
    )
    op.create_index(
        "ix_device_record_tenant_device_submit",
        "biz_device_record",
        ["tenant_id", "device_id", "submit_date"],
        unique=False,
    )

    op.alter_column("biz_device_record", "source", server_default=None)
    op.alter_column("biz_device_record", "process_result", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_device_record_tenant_device_submit", table_name="biz_device_record")
    op.drop_index("ix_device_record_tenant_type_submit", table_name="biz_device_record")

    op.drop_column("biz_device_record", "process_result")
    op.drop_column("biz_device_record", "trace_id")
    op.drop_column("biz_device_record", "source")
    op.drop_column("biz_device_record", "detail_json")

    op.drop_column("biz_device", "installed_at")
    op.drop_column("biz_device", "model")
    op.drop_column("biz_device", "vendor")
