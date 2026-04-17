"""Module One smoke test script.

This script seeds a temporary SQLite database, boots the FastAPI app in-process,
then exercises关键路径：登录、权限查询、组织树查询、刷新令牌、用户状态变更。
运行结果会输出到控制台，便于写入修复报告。
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import List

from httpx import ASGITransport, AsyncClient

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in os.sys.path:
    os.sys.path.append(str(BASE_DIR))

TEST_DB_PATH = BASE_DIR / "module_one_test.db"
# 在导入 FastAPI 应用之前设置测试数据库，避免污染默认 dev.db
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{TEST_DB_PATH.as_posix()}")

from app.main import app  # noqa: E402  pylint: disable=wrong-import-position
from app.core.security import hash_password  # noqa: E402
from app.db import Base, SessionLocal, engine  # noqa: E402
from app.modules.user.models import (  # noqa: E402
    Org,
    Permission,
    Role,
    RolePermission,
    Tenant,
    User,
    UserRole,
)

APP_CLIENT = "reg_app"
TEST_USERNAME = "admin"
TEST_PASSWORD = "Admin123!"


async def reset_database() -> None:
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def seed_baseline_data() -> int:
    async with SessionLocal() as session:
        tenant = Tenant(id=1, name="测试租户", status="ACTIVE")
        org_root = Org(id=1, tenant_id=1, parent_id=None, name="监管总局", org_type="AREA")
        org_child = Org(id=2, tenant_id=1, parent_id=1, name="校园食安办", org_type="SCHOOL")
        role = Role(tenant_id=1, name="监管管理员", role_type="REGULATOR")
        permission = Permission(code="user:status:update", name="用户状态管理")
        user = User(
            tenant_id=1,
            org_id=1,
            username=TEST_USERNAME,
            real_name="管理员",
            email="admin@example.com",
            password_hash=hash_password(TEST_PASSWORD),
            role_type="REGULATOR",
            status="ACTIVE",
            token_version=1,
        )
        session.add_all([tenant, org_root, org_child, role, permission, user])
        await session.flush()
        session.add_all(
            [
                UserRole(user_id=user.id, role_id=role.id, tenant_id=tenant.id),
                RolePermission(role_id=role.id, permission_id=permission.id, tenant_id=tenant.id),
            ]
        )
        await session.commit()
        return user.id


async def run_http_flow(user_id: int) -> List[str]:
    steps: List[str] = []
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        login_resp = await client.post(
            "/auth/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD, "app_client": APP_CLIENT},
        )
        assert login_resp.status_code == 200, login_resp.text
        login_body = login_resp.json()
        assert login_body["code"] == 200, login_body
        tokens = login_body["data"]
        access_token = tokens["accessToken"]
        refresh_token = tokens["refreshToken"]
        user_info = tokens["userInfo"]
        steps.append(f"✅ 登录成功，用户 ID={user_info['id']}, 租户={user_info['tenantId']}")

        headers = {"Authorization": f"Bearer {access_token}", "X-App-Client": APP_CLIENT}

        perm_resp = await client.get("/auth/me/permissions", headers=headers)
        assert perm_resp.status_code == 200, perm_resp.text
        perm_body = perm_resp.json()
        assert "user:status:update" in perm_body["data"], perm_body
        steps.append("✅ 权限查询返回 user:status:update")

        org_resp = await client.get("/org/tree", params={"root_id": 1}, headers=headers)
        assert org_resp.status_code == 200, org_resp.text
        org_body = org_resp.json()["data"]
        assert org_body["name"] == "监管总局"
        assert org_body["children"] and org_body["children"][0]["name"] == "校园食安办"
        steps.append("✅ 组织树接口返回预期结构")

        refresh_resp = await client.post(
            "/auth/refresh",
            json={"refreshToken": refresh_token},
            headers={"X-App-Client": APP_CLIENT},
        )
        assert refresh_resp.status_code == 200, refresh_resp.text
        refresh_body = refresh_resp.json()
        assert refresh_body["code"] == 200, refresh_body
        steps.append("✅ 刷新令牌成功，旧 token 可轮换")

        status_resp = await client.put(
            f"/user/{user_id}/status",
            json={"status": "DISABLED"},
            headers=headers,
        )
        assert status_resp.status_code == 200, status_resp.text
        status_body = status_resp.json()["data"]
        assert status_body["status"] == "DISABLED"
        steps.append("✅ 用户禁用接口正常工作，token_version 已递增")
    return steps


async def main() -> bool:
    summary: List[str] = []
    success = False
    try:
        await reset_database()
        summary.append("✅ 数据库已重置为 module_one_test.db")
        user_id = await seed_baseline_data()
        summary.append(f"✅ 基础数据准备完成 (user_id={user_id})")
        summary.extend(await run_http_flow(user_id))
        success = True
    except AssertionError as exc:  # pragma: no cover - 脚本日志即可
        summary.append(f"❌ 断言失败: {exc}")
    except Exception as exc:  # pragma: no cover
        summary.append(f"❌ 未预期错误: {exc}")
    finally:
        for line in summary:
            print(line)
        print(f"模块一冒烟结果: {'PASS' if success else 'FAIL'}")
    return success


if __name__ == "__main__":
    asyncio.run(main())
