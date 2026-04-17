from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from sqlalchemy import select

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from app.core.context import UserContext
from app.db import Base
from app.db.session import SessionLocal, engine
from app.modules.ledger.models import LedgerTemplate


TENANT_ID = 1

TEMPLATES = [
    {
        "title": "每日晨检表",
        "description": "测试模板-晨检",
        "schema": {
            "version": "v1",
            "fields": [
                {"field_id": "staff_name", "type": "string", "label": "员工姓名", "required": True},
                {"field_id": "temperature", "type": "number", "label": "体温(℃)", "required": True, "min": 34, "max": 43},
                {"field_id": "health_status", "type": "string", "label": "健康情况", "enum": ["正常", "异常"], "required": True},
            ],
        },
    },
    {
        "title": "留样记录表",
        "description": "测试模板-留样",
        "schema": {
            "version": "v1",
            "fields": [
                {"field_id": "dish_name", "type": "string", "label": "菜品名称", "required": True},
                {"field_id": "sample_weight", "type": "number", "label": "留样重量(g)", "required": True, "min": 0},
                {"field_id": "keeper", "type": "string", "label": "留样人"},
                {"field_id": "remark", "type": "string", "label": "备注"},
            ],
        },
    },
    {
        "title": "餐具消毒记录",
        "description": "测试模板-消毒",
        "schema": {
            "version": "v1",
            "fields": [
                {"field_id": "disinfect_method", "type": "string", "label": "消毒方式", "required": True},
                {"field_id": "start_time", "type": "string", "label": "开始时间", "required": True},
                {"field_id": "end_time", "type": "string", "label": "结束时间", "required": True},
                {"field_id": "operator", "type": "string", "label": "操作人"},
            ],
        },
    },
]


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    created = 0
    skipped = 0

    async with SessionLocal() as db:
        UserContext.set_tenant_id(str(TENANT_ID))
        try:
            for item in TEMPLATES:
                exists = (
                    await db.execute(
                        select(LedgerTemplate).where(
                            LedgerTemplate.tenant_id == TENANT_ID,
                            LedgerTemplate.title == item["title"],
                        )
                    )
                ).scalars().first()
                if exists:
                    skipped += 1
                    continue

                template = LedgerTemplate(
                    tenant_id=TENANT_ID,
                    title=item["title"],
                    description=item["description"],
                    schema=item["schema"],
                    hash=None,
                    is_deleted=False,
                    is_active=True,
                )
                db.add(template)
                created += 1

            await db.commit()
        finally:
            UserContext.reset()

    print(f"ledger templates created={created}, skipped={skipped}")


if __name__ == "__main__":
    asyncio.run(main())