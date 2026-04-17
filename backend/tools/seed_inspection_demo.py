from __future__ import annotations

import asyncio
from datetime import date, datetime

from sqlalchemy import select

from app.core.context import UserContext
from app.db.session import SessionLocal
from app.modules.inspection.models import (
    CompletionMethod,
    InspectionFormType,
    InspectionItem,
    InspectionResult,
    InspectionTask,
    InspectionTemplate,
    InspectionType,
    IssueType,
    MonthlyReport,
    ItemType,
)

DEMO_TENANT_ID = 1


async def seed_inspection_data() -> None:
    UserContext.set_tenant_id(str(DEMO_TENANT_ID))

    async with SessionLocal() as db:
        existing = (
            await db.execute(
                select(InspectionTemplate).where(
                    InspectionTemplate.tenant_id == DEMO_TENANT_ID,
                    InspectionTemplate.template_name == "DEMO 高中日管控检查表",
                )
            )
        ).scalars().first()
        if existing:
            print("巡检演示数据已存在，跳过插入")
            return
        daily_template = InspectionTemplate(
            tenant_id=DEMO_TENANT_ID,
            inspection_type=InspectionType.DAILY,
            template_name="DEMO 高中日管控检查表",
            executor_role="FOOD_SAFETY_DIRECTOR",
            approver_role="SUPERVISOR",
            start_time="06:00",
            end_time="20:00",
            target_node_ids_raw={"ids": ["canteen_101"]},
        )
        weekly_template = InspectionTemplate(
            tenant_id=DEMO_TENANT_ID,
            inspection_type=InspectionType.WEEKLY,
            template_name="DEMO 学校食堂春季食品安全周排查表",
            executor_role="FOOD_SAFETY_DIRECTOR",
            approver_role="SUPERVISOR",
            form_type=InspectionFormType.SCORE_SELECT,
            start_time="06:00",
            end_time="20:00",
            target_node_ids_raw={"ids": ["canteen_101"]},
        )

        db.add_all([daily_template, weekly_template])
        await db.flush()

        daily_item1 = InspectionItem(
            tenant_id=DEMO_TENANT_ID,
            template=daily_template,
            item_type=ItemType.ITEM,
            sort_order=1,
            content="每日完成晨检，人员人数及身体要求达标",
            completion_method=CompletionMethod.INPUT_REQUIRED,
        )
        daily_item2 = InspectionItem(
            tenant_id=DEMO_TENANT_ID,
            template=daily_template,
            item_type=ItemType.ITEM,
            sort_order=2,
            content="每日完成留样，早中晚已完成留样并达标",
            completion_method=CompletionMethod.PHOTO_REQUIRED,
        )

        weekly_group = InspectionItem(
            tenant_id=DEMO_TENANT_ID,
            template=weekly_template,
            item_type=ItemType.GROUP,
            sort_order=1,
            content="食材问题排查",
        )

        db.add_all([daily_item1, daily_item2, weekly_group])
        await db.flush()

        weekly_minor = InspectionItem(
            tenant_id=DEMO_TENANT_ID,
            template=weekly_template,
            parent=weekly_group,
            item_type=ItemType.ITEM,
            sort_order=1,
            content="食堂无三无、腐烂、过期食材",
            issue_type=IssueType.RED_LINE,
            total_score=6.0,
            scoring_options=[6.0, 3.0, 0.0],
        )

        db.add(weekly_minor)
        await db.flush()

        daily_form_snapshot = [
            {
                "item_id": daily_item1.id,
                "content": daily_item1.content,
                "completion_method": daily_item1.completion_method.value
                if daily_item1.completion_method
                else None,
            },
            {
                "item_id": daily_item2.id,
                "content": daily_item2.content,
                "completion_method": daily_item2.completion_method.value
                if daily_item2.completion_method
                else None,
            },
        ]

        weekly_form_snapshot = {
            "form_type": weekly_template.form_type.value
            if weekly_template.form_type
            else None,
            "major_items": [
                {
                    "title": weekly_group.content,
                    "minor_items": [
                        {
                            "item_id": weekly_minor.id,
                            "content": weekly_minor.content,
                            "issue_type": weekly_minor.issue_type.value
                            if weekly_minor.issue_type
                            else None,
                            "total_score": weekly_minor.total_score,
                            "scoring_options": weekly_minor.scoring_options,
                        }
                    ],
                }
            ],
        }

        base_date = date(2026, 1, 20)
        now = datetime.utcnow()

        daily_task_pending = InspectionTask(
            tenant_id=DEMO_TENANT_ID,
            inspection_type=InspectionType.DAILY,
            template=daily_template,
            business_date=base_date,
            canteen_id=101,
            canteen_name_snapshot="武尚一中一食堂",
            status="PENDING",
            total_items=2,
            finished_items=0,
            form_snapshot=daily_form_snapshot,
        )

        daily_task_submitted = InspectionTask(
            tenant_id=DEMO_TENANT_ID,
            inspection_type=InspectionType.DAILY,
            template=daily_template,
            business_date=base_date,
            canteen_id=101,
            canteen_name_snapshot="武尚一中一食堂",
            executor_id="user-canteen-liuneng",
            executor_name_snapshot="刘能",
            status="SUBMITTED",
            actual_start_time=now,
            submission_time=now,
            total_items=2,
            finished_items=2,
            form_snapshot=daily_form_snapshot,
        )

        weekly_task_rejected = InspectionTask(
            tenant_id=DEMO_TENANT_ID,
            inspection_type=InspectionType.WEEKLY,
            template=weekly_template,
            business_date=base_date,
            canteen_id=102,
            canteen_name_snapshot="武尚实验中学一食堂",
            executor_id="user-regulator-zhangsan",
            executor_name_snapshot="张三",
            status="REJECTED",
            actual_start_time=now,
            submission_time=now,
            total_score=89.0,
            red_line_issues=1,
            form_snapshot=weekly_form_snapshot,
        )

        weekly_task_rectified = InspectionTask(
            tenant_id=DEMO_TENANT_ID,
            inspection_type=InspectionType.WEEKLY,
            template=weekly_template,
            business_date=base_date,
            canteen_id=102,
            canteen_name_snapshot="武尚实验中学一食堂",
            executor_id="user-regulator-zhangsan",
            executor_name_snapshot="张三",
            status="RECTIFIED",
            actual_start_time=now,
            submission_time=now,
            rectified_time=now,
            total_score=80.0,
            red_line_issues=1,
            form_snapshot=weekly_form_snapshot,
        )

        db.add_all(
            [
                daily_task_pending,
                daily_task_submitted,
                weekly_task_rejected,
                weekly_task_rectified,
            ]
        )
        await db.flush()

        daily_result1 = InspectionResult(
            tenant_id=DEMO_TENANT_ID,
            task=daily_task_submitted,
            item=daily_item1,
            inspection_type=InspectionType.DAILY,
            is_qualified=False,
            inspection_description="晨检发现张三体温异常，已安排其离岗休息。",
            inspection_photos=["https://example.com/photo_daily_1.jpg"],
            has_issue=True,
        )
        daily_result2 = InspectionResult(
            tenant_id=DEMO_TENANT_ID,
            task=daily_task_submitted,
            item=daily_item2,
            inspection_type=InspectionType.DAILY,
            is_qualified=True,
            inspection_description="早餐留样20类，中餐留样40类。",
            inspection_photos=["https://example.com/photo_daily_2.jpg"],
            has_issue=False,
        )

        weekly_result_rejected = InspectionResult(
            tenant_id=DEMO_TENANT_ID,
            task=weekly_task_rejected,
            item=weekly_minor,
            inspection_type=InspectionType.WEEKLY,
            score_given=3.0,
            inspection_description="发现生鲜食材上有发芽情况。",
            inspection_photos=["https://example.com/photo_weekly_1.jpg"],
            has_issue=True,
            is_red_line_triggered=True,
        )

        weekly_result_rectified = InspectionResult(
            tenant_id=DEMO_TENANT_ID,
            task=weekly_task_rectified,
            item=weekly_minor,
            inspection_type=InspectionType.WEEKLY,
            score_given=3.0,
            inspection_description="发现生鲜食材上有发芽情况。",
            inspection_photos=["https://example.com/photo_weekly_2.jpg"],
            rectification_description="已将发芽土豆全部销毁并重新采购。",
            rectification_photos=["https://example.com/rectify_weekly_1.jpg"],
            rectified_at=now,
            has_issue=True,
            is_red_line_triggered=True,
        )

        db.add_all(
            [
                daily_result1,
                daily_result2,
                weekly_result_rejected,
                weekly_result_rectified,
            ]
        )

        monthly_report = MonthlyReport(
            tenant_id=DEMO_TENANT_ID,
            title="DEMO 2026年1月武尚一中月调度报告",
            reporter_id="user-director-wang",
            reporter_name_snapshot="食安总监",
            report_time=now,
            canteen_id=101,
            canteen_name_snapshot="武尚一中一食堂",
            source_config={
                "daily": {
                    "start_date": "2026-01-01",
                    "end_date": "2026-01-31",
                    "target_node_ids": ["canteen_101"],
                },
                "weekly": {
                    "start_date": "2026-01-01",
                    "end_date": "2026-01-31",
                    "target_node_ids": ["canteen_101"],
                },
            },
            system_report_markdown="# DEMO 月调度报告\n\n本报告基于示例巡检数据自动生成。",
        )

        db.add(monthly_report)

        await db.commit()


async def main() -> None:
    await seed_inspection_data()


if __name__ == "__main__":
    asyncio.run(main())