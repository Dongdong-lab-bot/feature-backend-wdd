"""Scene handler abstractions and registry for DataAgent."""

from abc import ABC, abstractmethod
import json
from typing import Any, Awaitable, Callable, Optional

from src.core.exceptions import (
    DBExecuteFailedError,
    ErrorCodeEnum,
    LLMCallFailedError,
    SQLPerformanceBlockedError,
    SQLSecurityBlockedError,
)
from src.core.schemas import AgentEventTypeEnum

from .audit import audit_log
from .models import HandlerContext


SCENE_HANDLER_REGISTRY: dict[str, type["BaseSceneHandler"]] = {}


def register_scene_handler(scene: str):
    """Decorator to register a scene handler class."""

    def _decorator(handler_cls: type["BaseSceneHandler"]):
        normalized_scene = scene.strip().lower()
        if not normalized_scene:
            raise ValueError("scene 不能为空")
        if normalized_scene in SCENE_HANDLER_REGISTRY:
            raise ValueError(f"scene '{normalized_scene}' 已注册")
        SCENE_HANDLER_REGISTRY[normalized_scene] = handler_cls
        return handler_cls

    return _decorator


class BaseSceneHandler(ABC):
    """Base class for all DataAgent scene handlers."""

    scene_name: str = ""

    def __init__(
        self,
        publisher: Optional[Callable[[AgentEventTypeEnum, dict[str, Any]], Awaitable[None]]] = None,
        sql_guard: Any = None,
    ) -> None:
        self._publisher = publisher
        self._sql_guard = sql_guard

    async def _publish_event(self, event_type: AgentEventTypeEnum, payload: dict[str, Any]) -> None:
        if self._publisher:
            await self._publisher(event_type, payload)

    @abstractmethod
    async def handle(self, user_query: str, context: HandlerContext) -> dict[str, Any]:
        """Handle user query with full handler context."""


@register_scene_handler("alarm_query")
class AlarmQueryHandler(BaseSceneHandler):
    """First scene handler: alarm data query flow."""

    scene_name = "alarm_query"

    async def handle(self, user_query: str, context: HandlerContext) -> dict[str, Any]:
        trace_id = context.trace_id

        audit_log(
            operator="data_agent",
            action="generate_sql",
            input_data=user_query,
            output_data="start",
            success=True,
            trace_id=trace_id,
        )
        try:
            llm_sql = self._mock_llm_generate_sql(user_query=user_query, trace_id=trace_id)
        except LLMCallFailedError as exc:
            await self._publish_event(
                AgentEventTypeEnum.SQL_GENERATED,
                {
                    "trace_id": trace_id,
                    "user_query": user_query,
                    "status": "failed",
                    "error_code": exc.error_code.value,
                    "message": exc.message,
                },
            )
            raise

        await self._publish_event(
            AgentEventTypeEnum.SQL_GENERATED,
            {
                "trace_id": trace_id,
                "user_query": user_query,
                "sql": llm_sql,
                "status": "success",
            },
        )

        audit_log(
            operator="data_agent",
            action="security_check",
            input_data=llm_sql,
            output_data="start",
            success=True,
            trace_id=trace_id,
        )
        # 通过 SQLGuard 执行安全校验（统一入口）
        guard_result = self._sql_guard.validate(llm_sql) if self._sql_guard else None
        if guard_result and guard_result.blocked:
            await self._publish_event(
                AgentEventTypeEnum.SQL_BLOCKED,
                {
                    "trace_id": trace_id,
                    "sql": llm_sql,
                    "blocked_reason": "security",
                    "error_code": ErrorCodeEnum.SQL_SECURITY_BLOCKED.value,
                    "message": guard_result.reason,
                },
            )
            raise SQLSecurityBlockedError(detail={"sql": llm_sql, "reason": guard_result.reason})

        audit_log(
            operator="data_agent",
            action="performance_check",
            input_data=llm_sql,
            output_data="start",
            success=True,
            trace_id=trace_id,
        )
        try:
            processed_sql = self._performance_check(sql=llm_sql, trace_id=trace_id)
        except SQLPerformanceBlockedError as exc:
            await self._publish_event(
                AgentEventTypeEnum.SQL_BLOCKED,
                {
                    "trace_id": trace_id,
                    "sql": llm_sql,
                    "blocked_reason": "performance",
                    "error_code": exc.error_code.value,
                    "message": exc.message,
                },
            )
            raise

        audit_log(
            operator="data_agent",
            action="db_execute",
            input_data=processed_sql,
            output_data="start",
            success=True,
            trace_id=trace_id,
        )
        rows = self._mock_execute_sql(sql=processed_sql, trace_id=trace_id)
        await self._publish_event(
            AgentEventTypeEnum.SQL_EXECUTED,
            {
                "trace_id": trace_id,
                "sql": processed_sql,
                "row_count": len(rows),
            },
        )

        return {
            "query": user_query,
            "sql": processed_sql,
            "rows": rows,
            "total": len(rows),
        }

    def _mock_llm_generate_sql(self, user_query: str, trace_id: str) -> str:
        lowered = user_query.lower()
        if "llm_fail" in lowered:
            audit_log(
                operator="data_agent",
                action="generate_sql",
                input_data=user_query,
                output_data="mock llm failure",
                success=False,
                trace_id=trace_id,
            )
            raise LLMCallFailedError("大模型调用失败")

        audit_log(
            operator="data_agent",
            action="generate_sql",
            input_data=user_query,
            output_data="sql generated",
            success=True,
            trace_id=trace_id,
        )
        return "SELECT id, alarm_type, created_at FROM alarms"

    def _performance_check(self, sql: str, trace_id: str) -> str:
        lowered = sql.lower()
        if " join " in lowered and " on " not in lowered:
            audit_log(
                operator="data_agent",
                action="performance_check",
                input_data=sql,
                output_data=ErrorCodeEnum.SQL_PERFORMANCE_BLOCKED.value,
                success=False,
                trace_id=trace_id,
            )
            raise SQLPerformanceBlockedError(detail={"sql": sql})

        processed_sql = sql if "limit" in lowered else f"{sql} LIMIT 100"
        audit_log(
            operator="data_agent",
            action="performance_check",
            input_data=sql,
            output_data=json.dumps({"processed_sql": processed_sql}, ensure_ascii=False),
            success=True,
            trace_id=trace_id,
        )
        return processed_sql

    def _mock_execute_sql(self, sql: str, trace_id: str) -> list[dict[str, Any]]:
        if "db_fail" in sql.lower():
            audit_log(
                operator="data_agent",
                action="db_execute",
                input_data=sql,
                output_data=ErrorCodeEnum.DB_EXECUTE_FAILED.value,
                success=False,
                trace_id=trace_id,
            )
            raise DBExecuteFailedError(detail={"sql": sql})

        rows = [
            {
                "id": "alarm_001",
                "alarm_type": "no_mask",
                "created_at": "2026-04-26T15:30:00+08:00",
            },
            {
                "id": "alarm_002",
                "alarm_type": "raw_food_mixed",
                "created_at": "2026-04-26T15:31:00+08:00",
            },
        ]
        audit_log(
            operator="data_agent",
            action="db_execute",
            input_data=sql,
            output_data=json.dumps({"row_count": len(rows)}, ensure_ascii=False),
            success=True,
            trace_id=trace_id,
        )
        return rows
