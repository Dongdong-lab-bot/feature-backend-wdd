import pytest
from sqlalchemy import create_engine, Column, Integer, String, text
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase, Mapped, mapped_column

# 适配 zzh 分支的新路径
from app.core.context import UserContext
from app.db.mixins import TenantMixin
from app.db.security_guard import register_security_guards, SecurityException

# 2. 定义一个测试用的临时 Model (模拟业务表)
class AcceptanceBase(DeclarativeBase):
    pass

class AcceptanceUser(AcceptanceBase, TenantMixin):
    __tablename__ = "test_acceptance_users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))

@pytest.fixture
def db_session():
    # 使用内存数据库模拟真实环境
    engine = create_engine("sqlite:///:memory:")
    AcceptanceBase.metadata.create_all(engine)
    
    # 🔥 核心：注册你的拦截器
    register_security_guards(None, engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    # 重置上下文
    UserContext.reset()
    
    yield session
    session.close()

# =============================================================================
# ✅ 验收标准 1: 自动填充
# 执行 session.add(User(name="test"))，落库后检查 tenant_id 是否正确填充。
# =============================================================================
def test_acceptance_criteria_1_auto_fill(db_session):
    # A. 模拟登录租户 1001
    # 注意：UserContext 接收 str 类型
    UserContext.set_tenant_id("1001")
    UserContext.set_user_id("1")
    UserContext.set_role_type("EXECUTOR")
    
    # B. 开发者写代码：只写 name，不写 tenant_id
    user = AcceptanceUser(name="test_worker")
    db_session.add(user)
    db_session.commit()
    
    # C. 验证：落库数据必须有 tenant_id (security_guard 会自动转回 int)
    db_session.refresh(user)
    assert user.tenant_id == 1001
    print("\n✅ [验收通过] 标准1: TenantID 自动填充成功")

# =============================================================================
# ✅ 验收标准 2: 原生 SQL 拦截
# 尝试执行 session.execute(text("SELECT * FROM users"))，期望抛出异常拦截。
# =============================================================================
def test_acceptance_criteria_2_block_raw_sql(db_session):
    # A. 模拟登录租户 1001
    UserContext.set_tenant_id("1001")
    UserContext.set_user_id("1")
    UserContext.set_role_type("EXECUTOR")
    
    # B. 开发者写了违规 SQL (没有 where tenant_id)
    raw_sql = text("SELECT * FROM test_acceptance_users")
    
    # C. 验证：必须抛出 SecurityException
    with pytest.raises(SecurityException) as excinfo:
        db_session.execute(raw_sql)
    
    assert "SECURITY BLOCK" in str(excinfo.value)
    print("\n✅ [验收通过] 标准2: 违规原生 SQL 成功被拦截")