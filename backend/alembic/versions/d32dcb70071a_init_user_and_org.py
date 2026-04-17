"""init_user_and_org

Revision ID: d32dcb70071a
Revises: None
Create Date: 2026-02-09 00:00:00
"""

from alembic import op
import sqlalchemy as sa

revision = 'd32dcb70071a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'organizations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('create_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('update_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('tenant_id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['parent_id'], ['organizations.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organizations_id'), 'organizations', ['id'], unique=False)
    op.create_index(op.f('ix_organizations_parent_id'), 'organizations', ['parent_id'], unique=False)
    op.create_index(op.f('ix_organizations_tenant_id'), 'organizations', ['tenant_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_organizations_tenant_id'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_parent_id'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_id'), table_name='organizations')
    op.drop_table('organizations')
