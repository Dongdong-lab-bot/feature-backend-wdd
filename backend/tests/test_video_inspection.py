from __future__ import annotations

import pathlib
import sys
from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from app.core.context import UserContext  # noqa: E402
from app.core.enums import InspectionTaskStatus  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.tenant_interceptor import TenantSession  # noqa: E402
from app.modules.inspection.models import (  # noqa: E402
    InspectionItem,
    InspectionResult,
    InspectionTask,
    InspectionTemplate,
    InspectionType,
    ItemType,
    IssueType,
)
from app.modules.inspection.schemas import (  # noqa: E402
    VideoTemplateRequest,
    WeeklyRectifyRequest,
    WeeklyInspectionSubmitRequest,
)
from app.modules.inspection.service import (  # noqa: E402
    InspectionTemplateService,
    InspectionWorkflow,
)
from app.modules.user.models import Org, Tenant  # noqa: E402
from app.modules.video.api import capture_video_frame, get_video_score_statistics  # noqa: E402
from app.modules.video.models import BizVideoCamera  # noqa: E402
from app.modules.video.schemas import VideoCaptureRequest  # noqa: E402


pytestmark = pytest.mark.asyncio


def login(tenant_id: int, user_id: int = 1) -> None:
    UserContext.set_tenant_id(str(tenant_id))
    UserContext.set_user_id(str(user_id))
    UserContext.set_role_type("REGULATOR")


@pytest_asyncio.fixture()
async def session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(
        bind=engine,
        class_=TenantSession,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        future=True,
    )

    async with Session() as db:
        try:
            yield db
        finally:
            UserContext.reset()

    await engine.dispose()


async def seed_tenant_org_tree(db: TenantSession, tenant_id: int) -> tuple[int, int]:
    login(tenant_id)
    db.add(Tenant(id=tenant_id, name=f"tenant-{tenant_id}", status="ACTIVE"))
    area_id = tenant_id * 100
    canteen_id = area_id + 1
    db.add(
        Org(
            id=area_id,
            tenant_id=tenant_id,
            parent_id=None,
            name=f"area-{tenant_id}",
            org_type="AREA",
            manager_id=None,
        )
    )
    db.add(
        Org(
            id=canteen_id,
            tenant_id=tenant_id,
            parent_id=area_id,
            name=f"canteen-{tenant_id}",
            org_type="CANTEEN",
            manager_id=None,
        )
    )
    await db.commit()
    return area_id, canteen_id


async def test_create_video_template_persists_associated_camera_ids(session):
    tenant_id = 1001
    area_id, _ = await seed_tenant_org_tree(session, tenant_id)
    current_user = SimpleNamespace(tenant_id=tenant_id)

    request = VideoTemplateRequest(
        template_name="视频巡检模板",
        executor_role="FOOD_SAFETY_DIRECTOR",
        approver_role="SUPERVISOR",
        target_node_ids=[area_id],
        start_time="06:00",
        end_time="20:00",
        form_type="SCORE_BASED",
        major_items=[
            {
                "sort_order": 1,
                "title": "后厨监控检查",
                "minor_items": [
                    {
                        "sort_order": 1,
                        "content": "食材留样柜状态正常",
                        "issue_type": "RED_LINE",
                        "total_score": 6,
                        "scoring_options": [6, 3, 0],
                        "associated_camera_ids": ["camera_001", "camera_002"],
                    }
                ],
            }
        ],
    )

    template = await InspectionTemplateService.create_video_template(
        session,
        current_user,
        request,
    )

    assert template.inspection_type == InspectionType.VIDEO

    stmt = select(InspectionItem).where(
        InspectionItem.template_id == template.id,
        InspectionItem.parent_item_id.is_not(None),
    )
    minor_item = (await session.execute(stmt)).scalars().one()
    assert minor_item.associated_camera_ids == ["camera_001", "camera_002"]


async def test_video_workflow_submit_rectify_audit(session):
    tenant_id = 1002
    _, canteen_id = await seed_tenant_org_tree(session, tenant_id)
    login(tenant_id)

    template = InspectionTemplate(
        tenant_id=tenant_id,
        inspection_type=InspectionType.VIDEO,
        template_name="视频巡检任务模板",
        form_type="SCORE_BASED",
        target_node_ids_raw={"raw": [canteen_id], "expanded_canteen_ids": [canteen_id]},
        is_active=True,
    )
    session.add(template)
    await session.flush()

    group_item = InspectionItem(
        tenant_id=tenant_id,
        template_id=template.id,
        item_type=ItemType.GROUP,
        sort_order=1,
        content="监控巡检",
    )
    session.add(group_item)
    await session.flush()

    minor_item = InspectionItem(
        tenant_id=tenant_id,
        template_id=template.id,
        parent_item_id=group_item.id,
        item_type=ItemType.ITEM,
        sort_order=1,
        content="通道无堆物",
        issue_type=IssueType.RED_LINE,
        total_score=6,
        scoring_options=[6, 3, 0],
        associated_camera_ids=["camera_003"],
    )
    session.add(minor_item)
    await session.flush()

    task = InspectionTask(
        tenant_id=tenant_id,
        inspection_type=InspectionType.VIDEO,
        template_id=template.id,
        business_date=date.today(),
        canteen_id=canteen_id,
        canteen_name_snapshot="测试食堂",
        status=InspectionTaskStatus.PENDING,
        form_snapshot={
            "form_type": "SCORE_BASED",
            "major_items": [
                {
                    "title": "监控巡检",
                    "minor_items": [
                        {
                            "item_id": minor_item.id,
                            "content": "通道无堆物",
                            "issue_type": "RED_LINE",
                            "total_score": 6,
                            "scoring_options": [6, 3, 0],
                            "associated_camera_ids": ["camera_003"],
                        }
                    ],
                }
            ],
        },
    )
    session.add(task)
    await session.commit()

    submit_request = WeeklyInspectionSubmitRequest(
        inspector_id="user-regulator-tester",
        actual_start_time=datetime.now(timezone.utc),
        results=[
            {
                "item_id": minor_item.id,
                "score_given": 0,
                "description": "通道被杂物占用",
                "photos": ["https://example.com/capture.jpg"],
            }
        ],
    )
    submitted = await InspectionWorkflow.submit_task(
        session,
        task.id,
        submit_request,
        idempotency_key="video-submit-1",
        inspection_type=InspectionType.VIDEO,
        inspector_name="监管员",
    )
    assert submitted.status == InspectionTaskStatus.SUBMITTED
    assert submitted.total_score == 0
    assert submitted.red_line_issues == 1

    result_stmt = select(InspectionResult).where(InspectionResult.task_id == task.id)
    result_row = (await session.execute(result_stmt)).scalars().one()
    assert result_row.inspection_type == InspectionType.VIDEO
    assert result_row.has_issue is True
    assert result_row.is_red_line_triggered is True

    rejected = await InspectionWorkflow.audit_task(
        session,
        task.id,
        auditor_id="auditor-1",
        action="REJECT",
        audit_opinion="请先整改后复审",
        idempotency_key="video-audit-reject-1",
        inspection_type=InspectionType.VIDEO,
    )
    assert rejected.status == InspectionTaskStatus.REJECTED

    rectify_request = WeeklyRectifyRequest(
        rectifier_id="canteen-user",
        feedback_per_item=[
            {
                "result_id": result_row.id,
                "description": "已完成清理",
                "photos": ["https://example.com/rectify.jpg"],
            }
        ],
    )
    rectified = await InspectionWorkflow.rectify_task(
        session,
        task.id,
        rectify_request,
        idempotency_key="video-rectify-1",
        inspection_type=InspectionType.VIDEO,
    )
    assert rectified.status == InspectionTaskStatus.RECTIFIED

    refreshed_result = (await session.execute(result_stmt)).scalars().one()
    assert refreshed_result.rectification_description == "已完成清理"
    assert refreshed_result.rectification_photos == ["https://example.com/rectify.jpg"]

    audited = await InspectionWorkflow.audit_task(
        session,
        task.id,
        auditor_id="auditor-1",
        action="PASS",
        audit_opinion="整改通过",
        idempotency_key="video-audit-1",
        inspection_type=InspectionType.VIDEO,
    )
    assert audited.status == InspectionTaskStatus.COMPLETED
    assert audited.completed_time is not None


async def test_capture_video_frame_success(session, tmp_path, monkeypatch):
    tenant_id = 1003
    _, canteen_id = await seed_tenant_org_tree(session, tenant_id)
    login(tenant_id)

    camera = BizVideoCamera(
        tenant_id=tenant_id,
        camera_id="camera_cap_001",
        device_serial="D20591677",
        channel_no="1",
        canteen_id=canteen_id,
        encrypt_enabled=False,
        is_active=True,
    )
    session.add(camera)
    await session.commit()

    async def allow_permission(*args, **kwargs):
        return None

    monkeypatch.setattr("app.modules.video.api._ensure_permission", allow_permission)
    monkeypatch.setattr("app.modules.video.api.settings.image_upload_dir", str(tmp_path))

    payload = VideoCaptureRequest(
        image_base64="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8Xw8AAoMBgQx5l1EAAAAASUVORK5CYII=",
        timestamp="2026-03-17T10:00:00Z",
    )
    current_user = SimpleNamespace(tenant_id=tenant_id, id=1, username="tester")

    response = await capture_video_frame(
        request=payload,
        camera_id="camera_cap_001",
        db=session,
        current_user=current_user,
    )

    assert response.code == 20000
    assert response.data is not None
    assert "photo_url" in response.data
    assert len(list(tmp_path.iterdir())) == 1


async def test_video_score_statistics_query(session, monkeypatch):
    tenant_id = 1004
    _, canteen_id = await seed_tenant_org_tree(session, tenant_id)
    login(tenant_id)

    template = InspectionTemplate(
        tenant_id=tenant_id,
        inspection_type=InspectionType.VIDEO,
        template_name="视频统计模板",
        form_type="SCORE_BASED",
        target_node_ids_raw={"raw": [canteen_id], "expanded_canteen_ids": [canteen_id]},
        is_active=True,
    )
    session.add(template)
    await session.flush()

    group_item = InspectionItem(
        tenant_id=tenant_id,
        template_id=template.id,
        item_type=ItemType.GROUP,
        sort_order=1,
        content="统计分组",
    )
    session.add(group_item)
    await session.flush()

    yellow_item = InspectionItem(
        tenant_id=tenant_id,
        template_id=template.id,
        parent_item_id=group_item.id,
        item_type=ItemType.ITEM,
        sort_order=1,
        content="黄线项",
        issue_type=IssueType.YELLOW_LINE,
        total_score=6,
        scoring_options=[6, 3, 0],
    )
    red_item = InspectionItem(
        tenant_id=tenant_id,
        template_id=template.id,
        parent_item_id=group_item.id,
        item_type=ItemType.ITEM,
        sort_order=2,
        content="红线项",
        issue_type=IssueType.RED_LINE,
        total_score=6,
        scoring_options=[6, 3, 0],
    )
    session.add_all([yellow_item, red_item])
    await session.flush()

    task = InspectionTask(
        tenant_id=tenant_id,
        inspection_type=InspectionType.VIDEO,
        template_id=template.id,
        business_date=date(2026, 3, 22),
        canteen_id=canteen_id,
        canteen_name_snapshot="武岗一食堂",
        status=InspectionTaskStatus.RECTIFIED,
        total_score=88,
        red_line_issues=1,
        submission_time=datetime(2026, 3, 22, 1, 0, 0, tzinfo=timezone.utc),
    )
    session.add(task)
    await session.flush()

    result_rows = [
        InspectionResult(
            tenant_id=tenant_id,
            task_id=task.id,
            item_id=yellow_item.id,
            inspection_type=InspectionType.VIDEO,
            has_issue=True,
            is_red_line_triggered=False,
            score_given=3,
        ),
        InspectionResult(
            tenant_id=tenant_id,
            task_id=task.id,
            item_id=red_item.id,
            inspection_type=InspectionType.VIDEO,
            has_issue=True,
            is_red_line_triggered=True,
            score_given=0,
        ),
    ]
    session.add_all(result_rows)
    await session.commit()

    async def allow_permission(*args, **kwargs):
        return None

    monkeypatch.setattr("app.modules.video.api._ensure_permission", allow_permission)

    current_user = SimpleNamespace(tenant_id=tenant_id, id=1, username="tester")
    response = await get_video_score_statistics(
        start_date="2026-03-01",
        end_date="2026-03-31",
        org_id=None,
        canteen_id=None,
        template_id=template.id,
        keyword="武岗",
        page=1,
        page_size=20,
        db=session,
        current_user=current_user,
    )

    assert response.code == 20000
    assert response.data is not None
    assert response.data["total"] == 1
    assert len(response.data["list"]) == 1
    row = response.data["list"][0]
    assert row["yellow_line_issues"] == 1
    assert row["red_line_issues"] == 1
    assert row["status"] == "RECTIFIED"
    assert row["submission_date"] == "2026-03-22"
