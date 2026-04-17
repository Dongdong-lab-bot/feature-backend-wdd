"""
给指定用户赋予全部权限（开发调试用）
用法: python tools/grant_super_permissions.py [username]
默认操作 test_exec 用户
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Base
from app.db.session import SessionLocal, engine
from app.modules.user.models import (
    Permission as PermissionModel,
    Role as RoleModel,
    RolePermission as RolePermissionModel,
    User as UserModel,
    UserRole as UserRoleModel,
)
from app.core.constants.permissions import PERMISSIONS_BY_MODULE
from app.core.context import system_mode_scope

TARGET_USERNAME = sys.argv[1] if len(sys.argv) > 1 else "test_exec"
SUPER_ROLE_NAME = "超级角色（全权限）"


async def ensure_all_permissions(db: AsyncSession) -> dict[str, int]:
    """确保所有权限都在 permissions 表中，返回 code->id 映射"""
    perm_map: dict[str, int] = {}
    for perms in PERMISSIONS_BY_MODULE.values():
        for code in perms:
            result = await db.execute(select(PermissionModel).where(PermissionModel.code == code))
            perm = result.scalar_one_or_none()
            if not perm:
                perm = PermissionModel(code=code, name=code)
                db.add(perm)
                await db.flush()
                print(f"  [新建权限] {code}")
            perm_map[code] = perm.id
    await db.commit()
    return perm_map


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    with system_mode_scope():
        async with SessionLocal() as db:
            # 1. 查找目标用户
            result = await db.execute(select(UserModel).where(UserModel.username == TARGET_USERNAME))
            user = result.scalar_one_or_none()
            if not user:
                print(f"错误：找不到用户 '{TARGET_USERNAME}'")
                return
            print(f"目标用户: id={user.id}, username={user.username}, tenant_id={user.tenant_id}")

            # 2. 确保所有权限记录存在
            print("\n同步权限表...")
            perm_map = await ensure_all_permissions(db)
            print(f"共 {len(perm_map)} 个权限")

            # 3. 找或创建超级角色
            result = await db.execute(
                select(RoleModel).where(
                    RoleModel.tenant_id == user.tenant_id,
                    RoleModel.name == SUPER_ROLE_NAME,
                )
            )
            role = result.scalar_one_or_none()
            if not role:
                role = RoleModel(
                    tenant_id=user.tenant_id,
                    name=SUPER_ROLE_NAME,
                    role_type="EXECUTOR",
                )
                db.add(role)
                await db.flush()
                print(f"\n[新建角色] id={role.id}, name={role.name}")
            else:
                print(f"\n[已存在角色] id={role.id}, name={role.name}")

            # 4. 给角色绑定全部权限
            added = 0
            for code, perm_id in perm_map.items():
                result = await db.execute(
                    select(RolePermissionModel).where(
                        RolePermissionModel.role_id == role.id,
                        RolePermissionModel.permission_id == perm_id,
                    )
                )
                if not result.scalar_one_or_none():
                    db.add(RolePermissionModel(
                        role_id=role.id,
                        permission_id=perm_id,
                        tenant_id=user.tenant_id,
                    ))
                    added += 1
            await db.commit()
            print(f"新增角色权限条目: {added} 条（已有的跳过）")

            # 5. 给用户绑定该角色
            result = await db.execute(
                select(UserRoleModel).where(
                    UserRoleModel.user_id == user.id,
                    UserRoleModel.role_id == role.id,
                )
            )
            if not result.scalar_one_or_none():
                db.add(UserRoleModel(
                    user_id=user.id,
                    role_id=role.id,
                    tenant_id=user.tenant_id,
                ))
                await db.commit()
                print(f"已绑定角色 '{SUPER_ROLE_NAME}' 到用户 '{TARGET_USERNAME}'")
            else:
                print(f"用户已拥有角色 '{SUPER_ROLE_NAME}'，无需重复绑定")

            print("\n✓ 完成！重新登录后权限生效。")


if __name__ == "__main__":
    asyncio.run(main())
