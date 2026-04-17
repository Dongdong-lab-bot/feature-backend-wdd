"""后端使用的 SQLAlchemy Engine 与 TenantSession 工厂。"""
from __future__ import annotations

from contextlib import contextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import settings
from app.db.tenant_interceptor import TenantSession

engine = create_async_engine(settings.database_url, future=True, echo=settings.sql_echo)
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=TenantSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[TenantSession, None]:
    # FastAPI 依赖项：为每个请求提供独立的 TenantSession
    async with SessionLocal() as db:
        yield db


__all__ = ["engine", "SessionLocal", "get_db"]
