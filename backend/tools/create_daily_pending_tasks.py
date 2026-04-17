from __future__ import annotations

import asyncio
from datetime import date
from typing import List, Optional

from sqlalchemy import select

from app.core.context import UserContext
from app.core.enums import InspectionTaskStatus
from app.db.session import SessionLocal
from app.modules.inspection.models import InspectionTask, InspectionTemplate, InspectionType

DEMO_TENANT_ID = 1


async def main() -> None:
    # 设置租户上下文（和接口、种子脚本保持一致）
    UserContext.set_tenant_id(str(DEMO_TENANT_ID))

    async with SessionLocal() as db:
        # 找一个日管控模板
        result = await db.execute(
            select(InspectionTemplate).where(
                InspectionTemplate.tenant_id == DEMO_TENANT_ID,
                InspectionTemplate.inspection_type == InspectionType.DAILY,
            )
        )
        template: Optional[InspectionTemplate] = result.scalars().first()
        if not template:
            print("未找到日管控模板（InspectionType.DAILY），请先运行 seed_inspection_demo 再重试。")
            return

        # 找一条现有日管控任务，用来复制食堂信息和 form_snapshot
        task_result = await db.execute(
            select(InspectionTask).where(
                InspectionTask.tenant_id == DEMO_TENANT_ID,
                InspectionTask.inspection_type == InspectionType.DAILY,
                InspectionTask.template_id == template.id,
            )
        )
        base_task: Optional[InspectionTask] = task_result.scalars().first()
        if not base_task:
            print("未找到现有日管控任务，无法复制 form_snapshot，请先通过脚本或接口创建一条任务。")
            return

        today = date.today()
        new_tasks: List[InspectionTask] = []

        for i in range(2):
            task = InspectionTask(
                tenant_id=DEMO_TENANT_ID,
                inspection_type=InspectionType.DAILY,
                template_id=template.id,
                business_date=today,
                canteen_id=base_task.canteen_id,
                canteen_name_snapshot=base_task.canteen_name_snapshot,
                status=InspectionTaskStatus.PENDING,
                total_items=base_task.total_items,
                finished_items=0,
                form_snapshot=base_task.form_snapshot,
            )
            new_tasks.append(task)

        db.add_all(new_tasks)
        await db.commit()

        print(
            f"已创建 {len(new_tasks)} 条日管控待检查任务："
            f"模板={template.template_name}, 食堂={base_task.canteen_name_snapshot}, 日期={today}"
        )


if __name__ == "__main__":
    asyncio.run(main())