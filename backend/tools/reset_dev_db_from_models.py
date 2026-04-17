from __future__ import annotations

import asyncio
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in os.sys.path:
    os.sys.path.insert(0, str(BASE_DIR))

DB_PATH = BASE_DIR / "dev.db"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{DB_PATH.as_posix()}"

from app.db import Base
from app.db.session import engine


async def main() -> None:
    # 删除旧的 dev.db（如果存在）
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"已删除旧的数据库文件: {DB_PATH}")

    # 按当前 ORM 模型创建所有表结构
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("已根据 ORM 模型创建所有表结构（users.email、refresh_tokens.family_id 等都会包含）")


if __name__ == "__main__":
    asyncio.run(main())