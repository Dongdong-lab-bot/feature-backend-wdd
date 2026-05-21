"""数据Agent - Pydantic模型（对齐全局Schema规范 V1.4）

所有核心模型从 src.core.schemas 导入，本模块仅定义内部组件专用模型。
"""

from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator
from src.core.schemas import TraceBase, SqlGenerationStatusEnum, SQLGenerateResult


# ============================================================
# 内部组件模型（非全局Schema，仅本组内部使用）
# ============================================================
class SQLGenerateRequest(BaseModel):
    """SQL生成请求模型（内部组件入参）"""
    user_query: str = Field(description="用户自然语言查询问题")
    schema_context: str = Field(description="表结构上下文，由 build_alert_table_schema() 生成或由 {{TABLE_SCHEMA}} 占位符填充")
    trace_id: str = Field(default="", description="全链路追踪ID")


class HandlerContext(BaseModel):
    """Context object passed through scene handlers.

    This model is intentionally stable to support future multi-turn dialogue and
    role-based filtering without changing function signatures.
    """

    trace_id: str = Field(..., min_length=1)
    user_role: str = Field(default="guest", min_length=1)
    store_ids: list[str] = Field(default_factory=list)
    chat_history: list[dict[str, Any]] = Field(default_factory=list)

    @field_validator("store_ids", mode="before")
    @classmethod
    def _normalize_store_ids(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("store_ids 必须为列表")
        normalized: list[str] = []
        for item in value:
            if item is None:
                raise ValueError("store_ids 不能为空")
            normalized.append(str(item))
        return normalized

    @field_validator("chat_history", mode="before")
    @classmethod
    def _normalize_chat_history(cls, value: Any) -> list[dict[str, Any]]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("chat_history 必须为列表")
        normalized: list[dict[str, Any]] = []
        for item in value:
            if isinstance(item, dict):
                normalized.append(item)
            else:
                normalized.append({"content": str(item)})
        return normalized
