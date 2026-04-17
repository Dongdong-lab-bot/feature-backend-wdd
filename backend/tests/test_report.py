import csv
import io
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db import Base, sync_engine, sync_db_session
from datetime import datetime, timedelta

from app.modules.ledger.models import ExportLog, LedgerInstance, LedgerStatus, LedgerTemplate
from app.modules.ledger.service import ReportService

# 创建测试客户端
client = TestClient(app)

TEST_TENANT_ID = 1001

# 测试前准备
@pytest.fixture(autouse=True)
def setup_db():
    # 创建测试数据库表
    Base.metadata.create_all(bind=sync_engine)
    yield
    # 测试后清理
    Base.metadata.drop_all(bind=sync_engine)


@pytest.fixture
def db():
    with sync_db_session() as session:
        yield session


@pytest_asyncio.fixture()
async def async_db():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    async with Session() as session:
        yield session

    await engine.dispose()

# 创建测试数据
@pytest.fixture
def ledger_template(db: Session):
    template = LedgerTemplate(
        tenant_id=TEST_TENANT_ID,
        title="报告测试模板",
        description="用于报表相关单测",
        schema={
            "fields": [
                {"field_id": "temperature", "label": "温度"},
                {"field_id": "inspector", "label": "检查人"},
            ]
        },
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@pytest.fixture
def test_ledgers(db: Session, ledger_template: LedgerTemplate):
    base_date = datetime(2024, 1, 1)
    schema_snapshot = {
        "fields": [
            {"field_id": "temperature", "label": "温度"},
            {"field_id": "inspector", "label": "检查人"},
        ]
    }
    # 创建测试台账实例
    ledger1 = LedgerInstance(
        canteen_id="canteen1",
        content={"temperature": "18", "inspector": "张三"},
        schema_snapshot=schema_snapshot,
        status=LedgerStatus.SIGNED,
        template_id=ledger_template.id,
        tenant_id=TEST_TENANT_ID,
        create_date=base_date,
    )
    ledger2 = LedgerInstance(
        canteen_id="canteen1",
        content={"temperature": "20", "inspector": "李四"},
        schema_snapshot=schema_snapshot,
        status=LedgerStatus.ARCHIVED,
        template_id=ledger_template.id,
        tenant_id=TEST_TENANT_ID,
        create_date=base_date + timedelta(days=1),
    )
    ledger3 = LedgerInstance(
        canteen_id="canteen2",
        content={"temperature": "15", "inspector": "王五"},
        schema_snapshot=schema_snapshot,
        status=LedgerStatus.PENDING,
        template_id=ledger_template.id,
        tenant_id=TEST_TENANT_ID,
        create_date=base_date + timedelta(days=2),
    )
    
    db.add_all([ledger1, ledger2, ledger3])
    db.commit()
    
    return [ledger1, ledger2, ledger3]

# 测试完成率统计接口
def test_compilation_report(test_ledgers):
    """
    测试完成率统计接口
    """
    response = client.get(
        "/report/compilation",
        params={
            "start_date": "2024-01-01",
            "end_date": "2024-12-31"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 20000
    assert data["msg"] == "success"

    payload = data["data"]
    assert payload["total_tasks"] == 3
    assert payload["completed_tasks"] == 2
    assert payload["status_stats"]["PENDING"] == 1
    assert payload["status_stats"]["SIGNED"] == 1
    assert payload["status_stats"]["ARCHIVED"] == 1
    assert payload["status_stats"]["FILLING"] == 0
    assert payload["completion_rate"] == pytest.approx(66.67, rel=1e-3)

# 测试报表导出接口
def test_export_report(test_ledgers, ledger_template: LedgerTemplate):
    """
    测试报表导出接口
    """
    response = client.get(
        "/report/export",
        params={
            "date": "2024-01-01",
            "template_id": ledger_template.id,
            "format": "excel"
        }
    )
    
    # 验证响应
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "Content-Disposition" in response.headers

    rows = list(csv.reader(io.StringIO(response.text)))
    assert rows[0] == ["台账ID", "食堂ID", "状态", "创建时间", "提交时间", "温度", "检查人"]
    assert rows[1][5:] == ["18", "张三"]

# 测试日期格式错误
def test_export_report_invalid_date(ledger_template: LedgerTemplate):
    """
    测试日期格式错误
    """
    response = client.get(
        "/report/export",
        params={
            "date": "2024/01/01",  # 错误的日期格式
            "template_id": ledger_template.id,
            "format": "excel"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 40002
    assert "invalid date format" in data["msg"]

# 测试状态值错误
def test_export_report_invalid_status(ledger_template: LedgerTemplate):
    """
    测试状态值错误
    """
    response = client.get(
        "/report/export",
        params={
            "date": "2024-01-01",
            "template_id": ledger_template.id,
            "status": "INVALID_STATUS",  # 错误的状态值
            "format": "excel"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 40002
    assert "invalid status value" in data["msg"]

# 测试模板ID缺失
def test_export_report_missing_template_id():
    """
    测试模板ID缺失
    """
    response = client.get(
        "/report/export",
        params={
            "date": "2024-01-01",
            "format": "excel"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 40004
    assert "export requires a single template" in data["msg"]


@pytest.mark.asyncio
async def test_record_export_log_async(async_db):
    log = await ReportService.record_export_log_async(
        async_db,
        user_id="tester",
        tenant_id="1001",
        export_date="2024-01-01",
        template_id=1,
        canteen_id=None,
        format="excel",
        record_count=5,
        ip_address="127.0.0.1",
        user_agent="pytest",
    )

    assert log.id is not None

    rows = await async_db.execute(select(ExportLog))
    entries = rows.scalars().all()
    assert len(entries) == 1
    assert entries[0].user_id == "tester"
