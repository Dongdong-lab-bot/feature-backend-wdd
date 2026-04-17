"""init

版本 ID: 74f8aad4bd97
上一个版本: 
创建时间: 2026-02-05 18:55:41.900810

"""
from typing import Sequence, Union
from datetime import datetime

from alembic import op
import sqlalchemy as sa


# 迁移脚本标识信息，供 Alembic 使用
revision: str = '74f8aad4bd97'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升级数据库结构。"""
    # ### 由 Alembic 自动生成的命令，可按需调整 ###
    op.create_table('permissions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=64), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code', name='uq_permission_code')
    )
    op.create_table('tenants',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.CheckConstraint("status in ('ACTIVE','DISABLED')", name='ck_tenant_status'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('orgs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('tenant_id', sa.Integer(), nullable=False),
    sa.Column('parent_id', sa.Integer(), nullable=True),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('org_type', sa.String(length=16), nullable=False),
    sa.Column('manager_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.CheckConstraint("org_type in ('AREA','SCHOOL','CANTEEN')", name='ck_org_type'),
    sa.ForeignKeyConstraint(['parent_id'], ['orgs.id'], ),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'parent_id', 'name', name='uq_org_name_parent')
    )
    op.create_index('ix_org_parent', 'orgs', ['parent_id'], unique=False)
    op.create_index('ix_org_tenant', 'orgs', ['tenant_id'], unique=False)
    op.create_table('roles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('tenant_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.Column('role_type', sa.String(length=16), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.CheckConstraint("role_type in ('REGULATOR','EXECUTOR')", name='ck_role_type'),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'name', name='uq_role_tenant_name')
    )
    op.create_index('ix_role_tenant', 'roles', ['tenant_id'], unique=False)
    op.create_table('role_permissions',
    sa.Column('role_id', sa.Integer(), nullable=False),
    sa.Column('permission_id', sa.Integer(), nullable=False),
    sa.Column('tenant_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
    sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )
    op.create_index('ix_role_permission_tenant', 'role_permissions', ['tenant_id'], unique=False)
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('tenant_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.Integer(), nullable=True),
    sa.Column('username', sa.String(length=64), nullable=False),
    sa.Column('real_name', sa.String(length=64), nullable=True),
    sa.Column('mobile', sa.String(length=32), nullable=True),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('role_type', sa.String(length=16), nullable=False),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('token_version', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.CheckConstraint("role_type in ('REGULATOR','EXECUTOR')", name='ck_user_role_type'),
    sa.CheckConstraint("status in ('ACTIVE','DISABLED')", name='ck_user_status'),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'username', name='uq_user_tenant_username')
    )
    op.create_index('ix_user_mobile', 'users', ['mobile'], unique=False)
    op.create_index('ix_user_org', 'users', ['org_id'], unique=False)
    op.create_index('ix_user_tenant', 'users', ['tenant_id'], unique=False)
    op.create_index('ix_user_tenant_mobile', 'users', ['tenant_id', 'mobile'], unique=False)
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("orgs") as batch_op:
            batch_op.create_foreign_key('fk_org_manager_user', 'users', ['manager_id'], ['id'])
        with op.batch_alter_table("users") as batch_op:
            batch_op.create_foreign_key('fk_user_org', 'orgs', ['org_id'], ['id'])
    else:
        op.create_foreign_key('fk_org_manager_user', 'orgs', 'users', ['manager_id'], ['id'])
        op.create_foreign_key('fk_user_org', 'users', 'orgs', ['org_id'], ['id'])
    op.create_table('external_identities',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('issuer', sa.String(length=255), nullable=False),
    sa.Column('subject', sa.String(length=255), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.Column('email', sa.String(length=255), nullable=True),
    sa.Column('raw_claims', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('issuer', 'subject', name='uq_external_issuer_subject')
    )
    op.create_index('ix_external_user', 'external_identities', ['user_id'], unique=False)
    op.create_table('user_roles',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('role_id', sa.Integer(), nullable=False),
    sa.Column('tenant_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'role_id')
    )
    op.create_index('ix_user_role_tenant', 'user_roles', ['tenant_id'], unique=False)
    tenants = sa.table(
        'tenants',
        sa.column('id', sa.Integer),
        sa.column('name', sa.String),
        sa.column('status', sa.String),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime),
    )
    orgs = sa.table(
        'orgs',
        sa.column('id', sa.Integer),
        sa.column('tenant_id', sa.Integer),
        sa.column('parent_id', sa.Integer),
        sa.column('name', sa.String),
        sa.column('org_type', sa.String),
        sa.column('manager_id', sa.Integer),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime),
    )
    permissions = sa.table(
        'permissions',
        sa.column('id', sa.Integer),
        sa.column('code', sa.String),
        sa.column('name', sa.String),
    )
    users = sa.table(
        'users',
        sa.column('id', sa.Integer),
        sa.column('tenant_id', sa.Integer),
        sa.column('org_id', sa.Integer),
        sa.column('username', sa.String),
        sa.column('real_name', sa.String),
        sa.column('mobile', sa.String),
        sa.column('password_hash', sa.String),
        sa.column('role_type', sa.String),
        sa.column('status', sa.String),
        sa.column('token_version', sa.Integer),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime),
    )
    roles = sa.table(
        'roles',
        sa.column('id', sa.Integer),
        sa.column('tenant_id', sa.Integer),
        sa.column('name', sa.String),
        sa.column('role_type', sa.String),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime),
    )
    role_permissions = sa.table(
        'role_permissions',
        sa.column('role_id', sa.Integer),
        sa.column('permission_id', sa.Integer),
        sa.column('tenant_id', sa.Integer),
    )
    user_roles = sa.table(
        'user_roles',
        sa.column('user_id', sa.Integer),
        sa.column('role_id', sa.Integer),
        sa.column('tenant_id', sa.Integer),
    )
    now = datetime.utcnow()
    op.bulk_insert(
        tenants,
        [
            {'id': 1, 'name': 'default', 'status': 'ACTIVE', 'created_at': now, 'updated_at': now},
        ],
    )
    op.bulk_insert(
        orgs,
        [
            {
                'id': 1,
                'tenant_id': 1,
                'parent_id': None,
                'name': '默认机构',
                'org_type': 'AREA',
                'manager_id': None,
                'created_at': now,
                'updated_at': now,
            },
        ],
    )
    op.bulk_insert(
        permissions,
        [
            {'id': 1, 'code': 'ledger:view', 'name': '查看台账'},
            {'id': 2, 'code': 'ledger:add', 'name': '新增台账'},
            {'id': 3, 'code': 'inspect:audit', 'name': '检查审核'},
            {'id': 4, 'code': 'ledger:submit', 'name': '提交台账'},
        ],
    )
    op.bulk_insert(
        users,
        [
            {
                'id': 1,
                'tenant_id': 1,
                'org_id': 1,
                'username': 'admin',
                'real_name': 'Admin',
                'mobile': None,
                'password_hash': '$pbkdf2-sha256$29000$g3CuVcqZE.JcK.U8p5SSUg$4aG3hpz.KltIiGkbN5Uvo7lPycY91hMo0F/Lgvz5I7s',
                'role_type': 'REGULATOR',
                'status': 'ACTIVE',
                'token_version': 1,
                'created_at': now,
                'updated_at': now,
            },
            {
                'id': 2,
                'tenant_id': 1,
                'org_id': 1,
                'username': 'executor',
                'real_name': 'Executor',
                'mobile': None,
                'password_hash': '$pbkdf2-sha256$29000$1fr/P4dwrvV.zznnvDcGgA$ZjZ.jrXme1lXzAHeU6c2CnO1aFKcResD.Gq12lQkO.Q',
                'role_type': 'EXECUTOR',
                'status': 'ACTIVE',
                'token_version': 1,
                'created_at': now,
                'updated_at': now,
            },
        ],
    )
    op.bulk_insert(
        roles,
        [
            {'id': 1, 'tenant_id': 1, 'name': '监管员', 'role_type': 'REGULATOR', 'created_at': now, 'updated_at': now},
            {'id': 2, 'tenant_id': 1, 'name': '执行员', 'role_type': 'EXECUTOR', 'created_at': now, 'updated_at': now},
        ],
    )
    op.bulk_insert(
        role_permissions,
        [
            {'role_id': 1, 'permission_id': 1, 'tenant_id': 1},
            {'role_id': 1, 'permission_id': 2, 'tenant_id': 1},
            {'role_id': 1, 'permission_id': 3, 'tenant_id': 1},
            {'role_id': 2, 'permission_id': 1, 'tenant_id': 1},
            {'role_id': 2, 'permission_id': 4, 'tenant_id': 1},
        ],
    )
    op.bulk_insert(
        user_roles,
        [
            {'user_id': 1, 'role_id': 1, 'tenant_id': 1},
            {'user_id': 2, 'role_id': 2, 'tenant_id': 1},
        ],
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """回退数据库结构。"""
    # ### 由 Alembic 自动生成的命令，可按需调整 ###
    op.drop_index('ix_user_role_tenant', table_name='user_roles')
    op.drop_table('user_roles')
    op.drop_index('ix_external_user', table_name='external_identities')
    op.drop_table('external_identities')
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("users") as batch_op:
            batch_op.drop_constraint('fk_user_org', type_='foreignkey')
        with op.batch_alter_table("orgs") as batch_op:
            batch_op.drop_constraint('fk_org_manager_user', type_='foreignkey')
    else:
        op.drop_constraint('fk_user_org', 'users', type_='foreignkey')
        op.drop_constraint('fk_org_manager_user', 'orgs', type_='foreignkey')
    op.drop_index('ix_user_tenant_mobile', table_name='users')
    op.drop_index('ix_user_tenant', table_name='users')
    op.drop_index('ix_user_org', table_name='users')
    op.drop_index('ix_user_mobile', table_name='users')
    op.drop_table('users')
    op.drop_index('ix_role_permission_tenant', table_name='role_permissions')
    op.drop_table('role_permissions')
    op.drop_index('ix_role_tenant', table_name='roles')
    op.drop_table('roles')
    op.drop_index('ix_org_tenant', table_name='orgs')
    op.drop_index('ix_org_parent', table_name='orgs')
    op.drop_table('orgs')
    op.drop_table('tenants')
    op.drop_table('permissions')
    # ### Alembic 命令结束 ###
