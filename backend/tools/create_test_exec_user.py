from __future__ import annotations

import asyncio
import os
from pathlib import Path

from sqlalchemy import select

# 确保可以从 backend 根目录导入 app 包
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in os.sys.path:
    os.sys.path.append(str(BASE_DIR))

from app.db import Base
from app.db.session import SessionLocal, engine
from app.modules.user.models import Tenant, Org, User
from app.core.security import hash_password


USERNAME = "test_exec"
PASSWORD = "Test123!"
TENANT_ID = 1
ORG_ID = 1


async def main() -> None:
    # 确保当前 dev.db 的表结构与 ORM 模型一致（开发环境允许直接 create_all）
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        tenant = await db.get(Tenant, TENANT_ID)
        if not tenant:
            tenant = Tenant(id=TENANT_ID, name="测试租户", status="ACTIVE")
            db.add(tenant)
            await db.flush()
            print(f"已创建租户: id={tenant.id}, name={tenant.name}")

        org = await db.get(Org, ORG_ID)
        if not org:
            org = Org(id=ORG_ID, tenant_id=TENANT_ID, parent_id=None, name="测试机构", org_type="AREA")
            db.add(org)
            await db.flush()
            print(f"已创建机构: id={org.id}, name={org.name}")

        result = await db.execute(select(User).where(User.username == USERNAME))
        user = result.scalar_one_or_none()
        if user:
            print(f"用户已存在: id={user.id}, username={user.username}")
        else:
            user = User(
                tenant_id=TENANT_ID,
                org_id=ORG_ID,
                username=USERNAME,
                real_name="Test Executor",
                email="test_exec@example.com",
                password_hash=hash_password(PASSWORD),
                role_type="EXECUTOR",
                status="ACTIVE",
                token_version=1,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            print(f"已创建用户: id={user.id}, username={user.username}")

        print()
        print("现在可以用以下信息登录：")
        print(f"  username = {USERNAME}")
        print(f"  password = {PASSWORD}")
        print("  app_client = exec_app")


if __name__ == "__main__":
    asyncio.run(main())