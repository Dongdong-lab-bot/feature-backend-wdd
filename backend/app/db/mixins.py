"""项目中复用的 SQLAlchemy Mixin 定义。"""
from __future__ import annotations

from typing import Set, Type

from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import declared_attr

TENANT_AWARE_MODELS: Set[Type] = set()


class TenantMixin:
    """为业务表强制注入租户编号字段的 Mixin。"""

    __abstract__ = True

    @declared_attr
    # SQLAlchemy 会在运行时注入该字段，需忽略静态类型检查
    def tenant_id(cls):  # type: ignore[misc]
        return Column(Integer, nullable=False, index=True, comment="租户ID")

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.__name__ == "TenantMixin":
            return
        # 仅注册真正声明了表名的模型
        if getattr(cls, "__tablename__", None):
            TENANT_AWARE_MODELS.add(cls)


__all__ = ["TenantMixin", "TENANT_AWARE_MODELS"]
