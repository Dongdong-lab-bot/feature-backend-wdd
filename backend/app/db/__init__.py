"""集中暴露常用 SQLAlchemy 对象，方便 FastAPI 依赖注入。"""

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.db.session import SessionLocal, engine, get_db

# 注册所有模型，确保 Base.metadata 包含所有表定义
import app.modules.user.models  # noqa: F401
import app.modules.ledger.models  # noqa: F401
import app.modules.video.models  # noqa: F401
import app.modules.inspection.models  # noqa: F401
import app.modules.device.models  # noqa: F401

# 同步 Session（用于遗留同步代码路径，例如台账/报表后台任务）
sync_engine = create_engine(
    settings.sync_database_url,
    future=True,
    echo=settings.sql_echo,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    class_=Session,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_sync_db():
    """FastAPI 依赖：提供同步 Session。"""
    db: Session = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def sync_db_session():
    """通过 with 语法获取同步 Session，便于脚本/测试覆盖。"""
    generator = get_sync_db()
    try:
        db = next(generator)
        yield db
    finally:
        generator.close()


__all__ = [
    "Base",
    "engine",
    "sync_engine",
    "SessionLocal",
    "get_db",
    "SyncSessionLocal",
    "get_sync_db",
    "sync_db_session",
]
