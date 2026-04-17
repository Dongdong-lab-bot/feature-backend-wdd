from __future__ import annotations

import asyncio
import os
from datetime import date, datetime
from pathlib import Path
from typing import List

from sqlalchemy import select

# 确保可以从 backend 根目录导入 app 包
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in os.sys.path:
    os.sys.path.append(str(BASE_DIR))

from app.core.context import UserContext
from app.db import Base
from app.db.session import SessionLocal, engine
from app.modules.ledger.constants import LedgerStatus
from app.modules.ledger.models import LedgerInstance, LedgerTask, LedgerTemplate
from app.modules.ledger.service import generate_daily_instances_for_canteens
from app.modules.user.models import Org


TENANT_ID = 1
BIZ_DATE = date.today()  # 生成今天的台账实例；调用接口时 date=今天 即可
MIN_CANTEEN_COUNT = 6
SIGNED_COUNT = 1


async def main() -> None:
    # 确保表结构存在（开发环境允许）
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        UserContext.set_tenant_id(str(TENANT_ID))
        try:
            # 1. 准备两个“食堂”机构（CANTEEN），挂在任意一个 AREA 下
            area_org = (
                await db.execute(
                    select(Org).where(Org.tenant_id == TENANT_ID, Org.org_type == "AREA")
                )
            ).scalars().first()
            if area_org is None:
                # 如果没有 AREA，就建一个默认的
                area_org = Org(
                    tenant_id=TENANT_ID,
                    name="默认区域",
                    org_type="AREA",
                    parent_id=None,
                )
                db.add(area_org)
                await db.flush()
                print(f"已创建 AREA 机构: id={area_org.id}, name={area_org.name}")

            canteens: List[Org] = (
                await db.execute(
                    select(Org).where(
                        Org.tenant_id == TENANT_ID,
                        Org.org_type == "CANTEEN",
                    )
                )
            ).scalars().all()

            if not canteens:
                c1 = Org(
                    tenant_id=TENANT_ID,
                    parent_id=area_org.id,
                    name="一号食堂",
                    org_type="CANTEEN",
                )
                c2 = Org(
                    tenant_id=TENANT_ID,
                    parent_id=area_org.id,
                    name="二号食堂",
                    org_type="CANTEEN",
                )
                db.add_all([c1, c2])
                await db.flush()
                canteens = [c1, c2]
                print(
                    "已创建食堂机构:",
                    ", ".join(f"{c.id}:{c.name}" for c in canteens),
                )
            else:
                print(
                    "已存在食堂机构:",
                    ", ".join(f"{c.id}:{c.name}" for c in canteens),
                )

            if len(canteens) < MIN_CANTEEN_COUNT:
                start_index = len(canteens) + 1
                extra = []
                for i in range(start_index, MIN_CANTEEN_COUNT + 1):
                    extra.append(
                        Org(
                            tenant_id=TENANT_ID,
                            parent_id=area_org.id,
                            name=f"测试食堂{i}",
                            org_type="CANTEEN",
                        )
                    )
                db.add_all(extra)
                await db.flush()
                canteens.extend(extra)
                print(
                    "已补充食堂机构:",
                    ", ".join(f"{c.id}:{c.name}" for c in extra),
                )

            canteen_ids = [c.id for c in canteens]

            # 2. 准备一个台账模板 + 调度任务
            template = (
                await db.execute(
                    select(LedgerTemplate).where(
                        LedgerTemplate.tenant_id == TENANT_ID,
                        LedgerTemplate.title == "每日晨检表",
                    )
                )
            ).scalars().first()

            if template is None:
                template = LedgerTemplate(
                    tenant_id=TENANT_ID,
                    title="每日晨检表",
                    schema={
                        "properties": {
                            "staffName": {"title": "员工姓名", "type": "string"},
                            "temperature": {"title": "体温(℃)", "type": "number"},
                            "healthStatus": {"title": "健康情况", "type": "string"},
                        }
                    },
                    hash=None,
                    is_deleted=False,
                )
                db.add(template)
                await db.flush()
                print(f"已创建模板: id={template.id}, title={template.title}")
            else:
                print(f"复用已存在模板: id={template.id}, title={template.title}")

            task = (
                await db.execute(
                    select(LedgerTask).where(
                        LedgerTask.tenant_id == TENANT_ID,
                        LedgerTask.template_id == template.id,
                    )
                )
            ).scalars().first()

            if task is None:
                task = LedgerTask(
                    tenant_id=TENANT_ID,
                    name="每日晨检任务",
                    template_id=template.id,
                    cron="0 8 * * *",
                    is_active=True,
                    target_config={"scope": "all_canteens"},
                )
                db.add(task)
                await db.flush()
                print(f"已创建任务: id={task.id}, name={task.name}")
            else:
                print(f"复用已存在任务: id={task.id}, name={task.name}")

            # 3. 生成当天的台账实例（PENDING）
            created = await generate_daily_instances_for_canteens(
                db, TENANT_ID, canteen_ids, BIZ_DATE
            )
            if created:
                print(f"已为 {len(canteen_ids)} 个食堂生成 {created} 条台账实例")
            else:
                print("今天的台账实例已存在，不再重复生成")

            # 4. 填充部分数据 & 标记部分为 SIGNED，让报表有“完成率”效果
            biz_dt = datetime(BIZ_DATE.year, BIZ_DATE.month, BIZ_DATE.day)

            instances: list[LedgerInstance] = (
                await db.execute(
                    select(LedgerInstance)
                    .where(
                        LedgerInstance.tenant_id == TENANT_ID,
                        LedgerInstance.template_id == template.id,
                        LedgerInstance.create_date == biz_dt,
                    )
                    .order_by(LedgerInstance.canteen_id, LedgerInstance.id)
                )
            ).scalars().all()

            if not instances:
                print("未找到当天的实例，可能生成步骤失败")
                return

            print(f"共找到 {len(instances)} 条 {BIZ_DATE.isoformat()} 的实例，开始填充示例数据...")

            for idx, inst in enumerate(instances):
                if idx < SIGNED_COUNT:
                    inst.status = LedgerStatus.SIGNED
                    inst.content = {
                        "staffName": f"张三-{inst.canteen_id}",
                        "temperature": 36.5 + (idx * 0.1),
                        "healthStatus": "正常",
                    }
                else:
                    inst.status = LedgerStatus.PENDING
                    inst.content = {
                        "staffName": f"李四-{inst.canteen_id}",
                        "temperature": None,
                        "healthStatus": "未检查",
                    }

            await db.commit()
            print("示例数据填充完成")
        finally:
            UserContext.reset()


if __name__ == "__main__":
    asyncio.run(main())