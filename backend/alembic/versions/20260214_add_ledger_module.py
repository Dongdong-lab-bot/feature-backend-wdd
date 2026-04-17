"""add ledger module

Revision ID: a1b2c3d4e5f6
Revises: None
Create Date: 2026-02-14 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '9b8d7c6e5f4a'  # 如果你有上一个版本文件，把那个文件的 revision ID 填在这
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. 创建模板表
    op.create_table('biz_ledger_template',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=100), nullable=False, comment='模板标题'),
        sa.Column('schema', sa.JSON(), nullable=False, comment='表单Schema定义'),
        sa.Column('hash', sa.String(length=64), nullable=True, comment='Schema哈希值'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, comment='软删除标记'),
        sa.Column('create_time', sa.DateTime(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False, comment='租户ID'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_biz_ledger_template_tenant_id'), 'biz_ledger_template', ['tenant_id'], unique=False)

    # 2. 创建任务表
    op.create_table('biz_ledger_task',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False, comment='任务名称'),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('cron', sa.String(length=50), nullable=False, comment='Cron表达式'),
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='是否启用'),
        sa.Column('target_config', sa.JSON(), nullable=False, comment='派发范围配置'),
        sa.Column('create_time', sa.DateTime(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False, comment='租户ID'),
        sa.ForeignKeyConstraint(['template_id'], ['biz_ledger_template.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_biz_ledger_task_tenant_id'), 'biz_ledger_task', ['tenant_id'], unique=False)

    # 3. 创建实例表
    op.create_table('biz_ledger_instance',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=True),
        sa.Column('canteen_id', sa.Integer(), nullable=False, comment='所属食堂ID'),
        sa.Column('status', sa.String(length=20), nullable=False, comment='状态'),
        sa.Column('schema_snapshot', sa.JSON(), nullable=False, comment='生成时的模板快照'),
        sa.Column('content', sa.JSON(), nullable=False, comment='填报内容'),
        sa.Column('security_hash', sa.String(length=64), nullable=True, comment='防篡改Hash'),
        sa.Column('signature_image', sa.String(length=255), nullable=True, comment='签字图片URL'),
        sa.Column('create_date', sa.DateTime(), nullable=False, comment='业务日期'),
        sa.Column('create_time', sa.DateTime(), nullable=False),
        sa.Column('submit_time', sa.DateTime(), nullable=True, comment='提交时间'),
        sa.Column('tenant_id', sa.Integer(), nullable=False, comment='租户ID'),
        sa.ForeignKeyConstraint(['task_id'], ['biz_ledger_task.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['biz_ledger_template.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_biz_ledger_instance_status'), 'biz_ledger_instance', ['status'], unique=False)
    
    # 4. 创建设备缓冲表 (新增)
    op.create_table('biz_device_buffer',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('device_uid', sa.String(length=64), nullable=False, comment='设备唯一标识'),
        sa.Column('raw_data', sa.JSON(), nullable=False, comment='硬件原始数据'),
        sa.Column('receive_time', sa.DateTime(), nullable=False),
        sa.Column('is_processed', sa.Boolean(), nullable=False),
        sa.Column('expire_time', sa.DateTime(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False, comment='租户ID'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_biz_device_buffer_device_uid'), 'biz_device_buffer', ['device_uid'], unique=False)


def downgrade() -> None:
    op.drop_table('biz_device_buffer')
    op.drop_table('biz_ledger_instance')
    op.drop_table('biz_ledger_task')
    op.drop_table('biz_ledger_template')