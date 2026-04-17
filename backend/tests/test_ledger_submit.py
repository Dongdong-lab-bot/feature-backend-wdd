import pytest
from sqlalchemy.orm import Session
import json
from app.db import Base, sync_engine, sync_db_session
from app.modules.ledger.models import LedgerInstance, LedgerStatus, LedgerTemplate
from app.modules.ledger.service import LedgerService, SALT
from app.modules.ledger.security import calculate_security_hash
from app.modules.ledger.form_engine import FieldValidationError


TEST_TENANT_ID = 1001


@pytest.fixture
def db():
    # 创建数据库表
    Base.metadata.create_all(bind=sync_engine)
    # 获取数据库会话
    try:
        with sync_db_session() as db:
            yield db
    finally:
        # 清理数据库表
        Base.metadata.drop_all(bind=sync_engine)


@pytest.fixture
def ledger_template(db: Session):
    template = LedgerTemplate(
        tenant_id=TEST_TENANT_ID,
        title="测试模板",
        description="用于单元测试",
        schema={"fields": [{"field_id": "data", "type": "string", "required": True}]},
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@pytest.fixture
def sample_ledger(db: Session, ledger_template: LedgerTemplate):
    # 创建测试台账
    ledger = LedgerInstance(
        canteen_id="test_canteen",
        content={"data": "test content"},
        schema_snapshot={"fields": [{"field_id": "data", "type": "string", "required": True}]},
        template_id=ledger_template.id,
        tenant_id=TEST_TENANT_ID,
    )
    db.add(ledger)
    db.commit()
    db.refresh(ledger)
    return ledger


@pytest.fixture
def complex_ledger(db: Session, ledger_template: LedgerTemplate):
    # 创建包含自动填充和验证规则的测试台账
    ledger = LedgerInstance(
        canteen_id="test_canteen",
        content={},
        schema_snapshot={
            "fields": [
                {"field_id": "name", "type": "string", "required": True, "minLength": 2},
                {"field_id": "age", "type": "number", "min": 18, "max": 100},
                {"field_id": "email", "type": "string", "regex": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"},
                {"field_id": "submit_time", "type": "string", "auto_fill": "current_time"},
                {"field_id": "canteen", "type": "string", "auto_fill": "canteen_name"},
                {"field_id": "submitter", "type": "string", "auto_fill": "user_name"},
                {"field_id": "status", "type": "string", "enum": ["OK", "NG"], "default": "OK"}
            ]
        },
        template_id=ledger_template.id,
        tenant_id=TEST_TENANT_ID,
    )
    db.add(ledger)
    db.commit()
    db.refresh(ledger)
    return ledger


def test_submit_ledger(db: Session, sample_ledger):
    """
    测试提交台账功能
    """
    # 新的内容
    new_content = {"data": "updated content"}
    
    # 提交台账
    updated_ledger = LedgerService.submit_ledger(db, sample_ledger.id, new_content)
    
    # 验证状态是否改为SIGNED
    assert updated_ledger.status == LedgerStatus.SIGNED
    
    # 验证内容是否更新
    assert updated_ledger.content == new_content
    
    # 验证security_hash是否计算正确
    expected_hash = calculate_security_hash(new_content, updated_ledger.schema_snapshot, SALT)
    assert updated_ledger.security_hash == expected_hash


def test_submit_signed_ledger(db: Session, sample_ledger):
    """
    测试提交已签名台账（应该失败）
    """
    # 先提交一次，使台账变为SIGNED状态
    LedgerService.submit_ledger(db, sample_ledger.id, {"data": "first submit"})
    
    # 再次尝试提交，应该抛出异常
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as excinfo:
        LedgerService.submit_ledger(db, sample_ledger.id, {"data": "second submit"})
    
    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "已签名台账无法修改"


def test_verify_ledger_integrity(db: Session, sample_ledger):
    """
    测试验证台账完整性
    """
    # 提交台账
    original_content = {"data": "original content"}
    LedgerService.submit_ledger(db, sample_ledger.id, original_content)
    
    # 验证完整性（应该通过）
    assert LedgerService.verify_ledger(db, sample_ledger.id) is True
    
    # 手动修改content，模拟篡改
    ledger = db.query(LedgerInstance).filter(LedgerInstance.id == sample_ledger.id).first()
    ledger.content = {"data": "tampered content"}
    db.commit()
    
    # 验证完整性（应该失败）
    assert LedgerService.verify_ledger(db, sample_ledger.id) is False


def test_tampering_detection(db: Session, sample_ledger):
    """
    测试篡改检测 - 手动篡改数据库content后，校验接口能发现hash不一致
    """
    # 提交台账
    original_content = {"data": "original content"}
    LedgerService.submit_ledger(db, sample_ledger.id, original_content)
    
    # 获取提交后的台账
    ledger = db.query(LedgerInstance).filter(LedgerInstance.id == sample_ledger.id).first()
    original_hash = ledger.security_hash
    
    # 验证完整性（应该通过）
    assert LedgerService.verify_ledger(db, sample_ledger.id) is True
    
    # 手动修改content，模拟篡改
    ledger.content = {"data": "tampered content"}
    db.commit()
    
    # 重新获取台账
    ledger = db.query(LedgerInstance).filter(LedgerInstance.id == sample_ledger.id).first()
    
    # 验证hash值没有改变（因为只修改了content，没有重新计算hash）
    assert ledger.security_hash == original_hash
    
    # 验证完整性（应该失败，因为hash不一致）
    assert LedgerService.verify_ledger(db, sample_ledger.id) is False
    
    # 验证重新计算的hash与存储的hash不一致
    current_hash = calculate_security_hash(ledger.content, ledger.schema_snapshot, SALT)
    assert current_hash != ledger.security_hash


def test_required_field_validation(db: Session, sample_ledger):
    """
    测试必填字段验证
    """
    # 尝试提交缺少必填字段的内容，应该抛出异常
    with pytest.raises(FieldValidationError) as excinfo:
        LedgerService.submit_ledger(db, sample_ledger.id, {})
    
    assert "Field 'data' is required" in str(excinfo.value)


def test_complex_validation(db: Session, complex_ledger):
    """
    测试复杂验证规则
    """
    # 测试验证失败的情况
    invalid_content = {"name": "a", "age": 17, "email": "invalid-email"}
    with pytest.raises(FieldValidationError):
        LedgerService.submit_ledger(db, complex_ledger.id, invalid_content)
    
    # 测试验证成功的情况
    valid_content = {"name": "John Doe", "age": 25, "email": "john@example.com"}
    updated_ledger = LedgerService.submit_ledger(db, complex_ledger.id, valid_content)
    
    # 验证状态是否改为SIGNED
    assert updated_ledger.status == LedgerStatus.SIGNED
    
    # 验证必填字段是否存在
    assert "name" in updated_ledger.content
    assert "age" in updated_ledger.content
    assert "email" in updated_ledger.content
    
    # 验证自动填充字段是否存在
    assert "submit_time" in updated_ledger.content
    assert "canteen" in updated_ledger.content
    assert "submitter" in updated_ledger.content
    assert updated_ledger.content["status"] == "OK"


def test_auto_fill_functions(db: Session, complex_ledger):
    """
    测试自动填充功能
    """
    # 提交只包含必填字段的内容
    content = {"name": "John Doe", "age": 25, "email": "john@example.com"}
    updated_ledger = LedgerService.submit_ledger(db, complex_ledger.id, content)
    
    # 验证自动填充字段是否被正确填充
    assert "submit_time" in updated_ledger.content
    assert len(updated_ledger.content["submit_time"]) > 0
    assert "canteen" in updated_ledger.content
    assert "submitter" in updated_ledger.content
    assert updated_ledger.content["status"] == "OK"


def test_enum_and_default_integration(db: Session, complex_ledger):
    """验证默认值回填与 enum 校验在服务层也生效。"""

    invalid_payload = {"name": "John", "age": 30, "email": "john@example.com", "status": "PENDING"}
    with pytest.raises(FieldValidationError):
        LedgerService.submit_ledger(db, complex_ledger.id, invalid_payload)

    payload_without_status = {"name": "John", "age": 30, "email": "john@example.com"}
    ledger = LedgerService.submit_ledger(db, complex_ledger.id, payload_without_status)

    assert ledger.content["status"] == "OK"
