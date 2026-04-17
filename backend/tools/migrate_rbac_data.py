"""
RBAC数据迁移脚本：将现有的role_id和permissions_desc数据迁移到多对多关系表

此脚本执行以下操作：
1. 初始化权限数据到permissions表
2. 将users.role_id迁移到user_roles表
3. 将roles.permissions_desc迁移到role_permissions表
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.constants.permissions import PERMISSIONS_BY_MODULE
from app.db.session import get_db_url
from app.modules.user.models import (
    Permission as PermissionModel,
    Role as RoleModel,
    RolePermission as RolePermissionModel,
    User as UserModel,
    UserRole as UserRoleModel,
)

settings = get_settings()


async def migrate_permissions(db: AsyncSession) -> dict:
    """初始化权限数据到permissions表"""
    print("开始迁移权限数据...")
    permission_map = {}
    
    for module, permissions in PERMISSIONS_BY_MODULE.items():
        for permission_code in permissions:
            existing = await db.execute(
                select(PermissionModel).where(PermissionModel.code == permission_code)
            )
            existing_permission = existing.scalar_one_or_none()
            
            if not existing_permission:
                permission = PermissionModel(
                    code=permission_code,
                    name=permission_code
                )
                db.add(permission)
                await db.flush()
                permission_map[permission_code] = permission.id
                print(f"  创建权限: {permission_code}")
            else:
                permission_map[permission_code] = existing_permission.id
    
    await db.commit()
    print(f"权限数据迁移完成，共 {len(permission_map)} 个权限")
    return permission_map


async def migrate_user_roles(db: AsyncSession) -> int:
    """将users.role_id迁移到user_roles表"""
    print("\n开始迁移用户角色关系...")
    
    result = await db.execute(
        select(UserModel).where(UserModel.role_id.isnot(None))
    )
    users = result.scalars().all()
    
    migrated_count = 0
    for user in users:
        existing = await db.execute(
            select(UserRoleModel).where(
                UserRoleModel.user_id == user.id,
                UserRoleModel.role_id == user.role_id,
                UserRoleModel.tenant_id == user.tenant_id
            )
        )
        existing_user_role = existing.scalar_one_or_none()
        
        if not existing_user_role:
            user_role = UserRoleModel(
                user_id=user.id,
                role_id=user.role_id,
                tenant_id=user.tenant_id
            )
            db.add(user_role)
            migrated_count += 1
            print(f"  迁移用户角色关系: 用户ID {user.id} -> 角色ID {user.role_id}")
    
    await db.commit()
    print(f"用户角色关系迁移完成，共迁移 {migrated_count} 条记录")
    return migrated_count


async def migrate_role_permissions(db: AsyncSession, permission_map: dict) -> int:
    """将roles.permissions_desc迁移到role_permissions表"""
    print("\n开始迁移角色权限关系...")
    
    result = await db.execute(
        select(RoleModel).where(RoleModel.permissions_desc.isnot(None))
    )
    roles = result.scalars().all()
    
    migrated_count = 0
    for role in roles:
        if not role.permissions_desc:
            continue
        
        permissions_desc = role.permissions_desc.strip()
        if not permissions_desc:
            continue
        
        permission_codes = [p.strip() for p in permissions_desc.split(',') if p.strip()]
        
        for permission_code in permission_codes:
            permission_id = permission_map.get(permission_code)
            if not permission_id:
                print(f"  警告: 权限代码 {permission_code} 不存在，跳过")
                continue
            
            existing = await db.execute(
                select(RolePermissionModel).where(
                    RolePermissionModel.role_id == role.id,
                    RolePermissionModel.permission_id == permission_id,
                    RolePermissionModel.tenant_id == role.tenant_id
                )
            )
            existing_role_permission = existing.scalar_one_or_none()
            
            if not existing_role_permission:
                role_permission = RolePermissionModel(
                    role_id=role.id,
                    permission_id=permission_id,
                    tenant_id=role.tenant_id
                )
                db.add(role_permission)
                migrated_count += 1
                print(f"  迁移角色权限关系: 角色ID {role.id} -> 权限 {permission_code}")
    
    await db.commit()
    print(f"角色权限关系迁移完成，共迁移 {migrated_count} 条记录")
    return migrated_count


async def main():
    """主函数"""
    print("=" * 60)
    print("RBAC数据迁移脚本")
    print("=" * 60)
    
    db_url = get_db_url()
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        try:
            permission_map = await migrate_permissions(db)
            user_roles_count = await migrate_user_roles(db)
            role_permissions_count = await migrate_role_permissions(db, permission_map)
            
            print("\n" + "=" * 60)
            print("数据迁移完成！")
            print(f"  权限数据: {len(permission_map)} 个")
            print(f"  用户角色关系: {user_roles_count} 条")
            print(f"  角色权限关系: {role_permissions_count} 条")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n错误: 迁移过程中发生异常")
            print(f"异常信息: {str(e)}")
            import traceback
            traceback.print_exc()
            await db.rollback()
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())